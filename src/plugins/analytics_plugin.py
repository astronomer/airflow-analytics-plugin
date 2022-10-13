import logging
from typing import Any

from sqlalchemy import text

from flask import Blueprint, request
from flask_appbuilder import BaseView as AppBuilderBaseView
from flask_appbuilder import expose

from airflow import configuration
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
airflow_webserver_base_url = configuration.get('webserver', 'BASE_URL')

apis_metadata = [
        {
        "name": "tasks",
        "description": "return number of successful and failed tasks for specified time period",
        "airflow_version": "xxx",  # airflow.version something like that
        "http_method": ["GET"],
        "arguments": [
           {"name": "startDate",
                "description": "The start date of the task period (Example: YYYY-MM-DD )", "form_input_type": "text", "required": True},
           {"name": "endDate",
                "description": "The end date of the task period (Example: YYYY-MM-DD)", "form_input_type": "text", "required": True},

       ]
    }
]


@provide_session
def dags_report(session) -> Any:
    untrusted_start_date = request.args.get("startDate") # 2022-08-01
    untrusted_end_date = request.args.get("endDate") #2022-08-30
    try:
        parse(untrusted_start_date)
        parse(untrusted_end_date)
    except ValueError:
        log.error("The string is not a date ")
    else:
        # remove the dummy operator and the astronomer_monitoring_dag that is added in runtime from task count
        query = (
            session.query(
                Log.event,
                func.count(Log.event).label("totalCount"),
            )
            .join(
                TaskInstance.event.in_(TaskInstanceState.SUCCESS, TaskInstanceState.FAILED),
                TaskInstance.operator != 'DummyOperator',
                TaskInstance.task_id == Log.task_id,
            )
            .filter(
                Log.dttm >= start_date,
                Log.dttm <= end_date,
                Log.dag_id != "astronomer_monitoring_dag",
            )
            .group_by(Log.event)
        )

        return [dict(result_row) for result_row in session.query(query).all()]



def format_db_response(resp):
    log.info(resp)
    task_summary_arr = resp["dags_report"]

    key_conversion = {
        'success': 'total_success',
        'failed': 'total_failed'
    }
    temp_result = {}
    for date_task_summary in task_summary_arr:
        fieldName = key_conversion[date_task_summary['event']]
        temp_result[fieldName]=date_task_summary['totalcount']

    return temp_result


rest_api_endpoint = "/astronomeranalytics/api/v1/"


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
        return self.render_template("/analytics_plugin/index.html",
            airflow_webserver_base_url=airflow_webserver_base_url,
            rest_api_endpoint=rest_api_endpoint,
            apis_metadata=apis_metadata,
        )

    @expose("api/v1/tasks")
    def tasks(self):
        dags = try_reporter(dags_report)

        if dags["dags_report"] == None:
            return {
                "message": "Invalid date",
            }
        return  {
            f"dags": format_db_response(dags)
        }


# Defining the plugin class
class AstronomerPlugin(AirflowPlugin):
    name = "AstronomerAnalytics"
    hooks = []
    macros = []
    flask_blueprints = [bp]
    appbuilder_views = [
        {
            "name": "API's",
            "category": "AstronomerAnalytics",
            "view": AstronomerAnalytics(),
        }
    ]
    appbuilder_menu_items = []
    global_operator_extra_links = []
    operator_extra_links = []
