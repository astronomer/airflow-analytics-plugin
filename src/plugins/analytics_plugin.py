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
        log_success = aliased(Log, name="log_success")
        log_failed = aliased(Log, name="log_failed")
        # remove the dummy operator and the astronomer_monitoring_dag that is added in runtime from task count
        query = (
            session.query(
                func.count(distinct(log_success.id)).label("total_success"),
                func.count(distinct(log_failed.id)).label("total_failed"),
            )
            .select_from(TaskInstance)
            .outerjoin(
                log_success,
                and_(
                    log_success.task_id == TaskInstance.task_id,
                    log_success.dttm >= start_date,
                    log_success.dttm <= end_date,
                    log_success.dag_id != "astronomer_monitoring_dag",
                    log_success.event == TaskInstanceState.SUCCESS,
                ),
                isouter=True,
            )
            .outerjoin(
                log_failed,
                and_(
                    log_failed.task_id == TaskInstance.task_id,
                    log_failed.dttm >= start_date,
                    log_failed.dttm <= end_date,
                    log_failed.dag_id != "astronomer_monitoring_dag",
                    log_success.event == TaskInstanceState.FAILED,
                ),
                isouter=True,
            )
            .filter(TaskInstance.operator != "DummyOperator")
        )

        return dict(session.query(query).one())


def try_reporter(reporter_func):
    try:
        rtn = {
            "results": reporter_func(),
        }
    except Exception as e:
        logging.exception(f"Failed reporting {reporter_func.__name__}")
        rtn = {
            "error": str(e),
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
                    "airflow_version": airflow_version,
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
            "tasks": try_reporter(tasks_report),
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
