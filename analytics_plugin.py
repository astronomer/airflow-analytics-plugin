import logging
from typing import Any

from sqlalchemy import and_, distinct, func, text
from sqlalchemy.orm import aliased

from flask import Blueprint, request
from flask_appbuilder import BaseView as AppBuilderBaseView
from flask_appbuilder import expose

from airflow import __version__ as airflow_version, configuration
from airflow.models import Log, TaskInstance
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.session import provide_session
from airflow.utils.state import TaskInstanceState
from airflow.utils.timezone import parse

__version__ = "1.0.0"

log = logging.getLogger(__name__)

bp = Blueprint(
    "astronomer_analytics",
    __name__,
    template_folder="templates",  # registers airflow/plugins/templates as a Jinja template folder
    static_folder="static",
    static_url_path="/static/",
)

airflow_webserver_base_url = configuration.get("webserver", "BASE_URL")


@provide_session
def tasks_report(session) -> Any:
    untrusted_start_date = request.args.get("startDate")  # 2022-08-01
    untrusted_end_date = request.args.get("endDate")  # 2022-08-30
    try:
        start_date = parse(untrusted_start_date)
        end_date = parse(untrusted_end_date)
    except ValueError as e:
        log.error(f"The string is not a date: {e}")
        raise e
    else:
        # remove the dummy operator and the astronomer_monitoring_dag that is added in runtime from task count
        query = (
            session.query(
                Log.event.label("event"),
                func.count(Log.id).label("totalCount"),
            )
            .select_from(Log)
            .join(
                TaskInstance,
                and_(
                    Log.event.in_(
                        [
                            TaskInstanceState.SUCCESS,
                            TaskInstanceState.FAILED,
                        ]
                    ),
                    Log.dttm >= start_date,
                    Log.dttm <= end_date,
                    TaskInstance.operator != "DummyOperator",
                    TaskInstance.operator != "EmptyOperator",
                    Log.dag_id != "astronomer_monitoring_dag",
                    TaskInstance.task_id == Log.task_id,
                ),
            )
            .group_by(Log.event)
        )
        return dict(query.all())


def format_db_response(resp):
    log.info(resp)
    task_summary = resp["tasks_report"]

    key_conversion = {"success": "total_success", "failed": "total_failed"}
    temp_result = {}
    for query_field in task_summary.keys():
        temp_result[key_conversion[query_field]] = task_summary[query_field]

    return temp_result


def try_reporter(reporter_func):
    try:
        rtn = {
            reporter_func.__name__: reporter_func(),
        }
    except Exception as e:
        logging.exception(f"Failed reporting {reporter_func.__name__}")
        rtn = {
            reporter_func.__name__: str(e),
        }
    return rtn


# Creating a flask appbuilder BaseView
class AstronomerAnalytics(AppBuilderBaseView):
    default_view = "index"

    @expose("/")
    def index(self):
        return self.render_template(
            "/analytics_plugin/index.html",
            airflow_webserver_base_url=airflow_webserver_base_url,
            rest_api_endpoint="/astronomeranalytics/api/v1/",
            apis_metadata=[
                {
                    "name": "tasks",
                    "description": "return number of successful and failed tasks for specified time period",
                    "airflow_version": "2.x",
                    "http_method": ["GET"],
                    "arguments": [
                        {
                            "name": "startDate",
                            "description": "The start date of the task period (Example: YYYY-MM-DD )",
                            "form_input_type": "text",
                            "required": True,
                        },
                        {
                            "name": "endDate",
                            "description": "The end date of the task period (Example: YYYY-MM-DD)",
                            "form_input_type": "text",
                            "required": True,
                        },
                    ],
                }
            ],
        )

    @expose("api/v1/tasks")
    def tasks(self):
        return {
            "tasks": format_db_response(try_reporter(tasks_report)),
        }


# Defining the plugin class
class AstronomerPlugin(AirflowPlugin):
    name = "Astronomer Analytics"
    hooks = []
    macros = []
    flask_blueprints = [bp]
    appbuilder_views = [
        {
            "name": "APIs",
            "category": "Astronomer Analytics",
            "view": AstronomerAnalytics(),
        }
    ]
    appbuilder_menu_items = []
    global_operator_extra_links = []
    operator_extra_links = []
