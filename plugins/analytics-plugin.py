from typing import Any 
from datetime import datetime

import logging
from sqlalchemy import text

from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint, request
from flask_appbuilder import BaseView as AppBuilderBaseView 
from flask_appbuilder import expose
from airflow import configuration
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
        "airflow_version": "xxx",
        "http_method": ["GET"],
        "arguments": [
           {"name": "startDate",
                "description": "The start date of the task period (Example: YYYY-MM-DD )", "form_input_type": "text", "required": True},
           {"name": "endDate",
                "description": "The end date of the task period (Example: YYYY-MM-DD)", "form_input_type": "text", "required": True},
 
       ]
    }
]
try:
    from airflow.utils.session import provide_session
except:
    from typing import Callable, Iterator, TypeVar

    import contextlib
    from functools import wraps
    from inspect import signature

    from airflow import DAG, settings

    RT = TypeVar("RT")

    def find_session_idx(func: Callable[..., RT]) -> int:
        """Find session index in function call parameter."""
        func_params = signature(func).parameters
        try:
            # func_params is an ordered dict -- this is the "recommended" way of getting the position
            session_args_idx = tuple(func_params).index("session")
        except ValueError:
            raise ValueError(f"Function {func.__qualname__} has no `session` argument") from None

        return session_args_idx

    @contextlib.contextmanager
    def create_session():
        """Contextmanager that will create and teardown a session."""
        session = settings.Session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def provide_session(func: Callable[..., RT]) -> Callable[..., RT]:
        """
        Function decorator that provides a session if it isn't provided.
        If you want to reuse a session or run the function as part of a
        database transaction, you pass it to the function, if not this wrapper
        will create one and close it for you.
        """
        session_args_idx = find_session_idx(func)

        @wraps(func)
        def wrapper(*args, **kwargs) -> RT:
            if "session" in kwargs or session_args_idx < len(args):
                return func(*args, **kwargs)
            else:
                with create_session() as session:
                    return func(*args, session=session, **kwargs)

        return wrapper

@provide_session
def dags_report(session) -> Any:
    format_YYYYMMDD = "%Y-%m-%d"
    start_date_input = request.args.get("startDate") # 2022-08-01
    end_date_input = request.args.get("endDate") #2022-08-30
    try:
        start_date = datetime.strptime(start_date_input, format_YYYYMMDD)
        end_date = datetime.strptime(end_date_input, format_YYYYMMDD)
        # remove the dummy operator and the astronomer_monitoring_dag that is added in runtime from task count
        sql = text(
            f"""
            select date::date, totalCount, event
            from generate_series('2022-09-01', '2022-09-30', '1 day'::interval) date
            left join 
                (select event, dttm::date, count(*) as totalCount from log l join task_instance ti on event in ('success', 'cli_task_run') and l.dttm >= '2022-09-01' and l.dttm <= '2022-09-30'  and l.dag_id != 'astronomer_monitoring_dag' and ti.task_id = l.task_id group by event, dttm::date ) t 
                on t.dttm::date = date.date
        """
        )
        return [dict(r) for r in session.execute(sql)]

    except ValueError:
        print("The string is not a date with format " + format_YYYYMMDD)

def format_db_response(resp):
    task_summary_arr = resp["dags_report"]
    key_conversion = {
        'success': 'total_success',
        'error': 'total_failed'
    }
    temp_result = {}
    for date_task_summary in task_summary_arr:
        dateStr = date_task_summary['date'].strftime("%Y-%m-%d")
        if dateStr not in temp_result:
            temp_result[dateStr] = {'total_success': 0, 'total_failed': 0}
        elif date_task_summary['event'] != None:
            fieldName = key_conversion[date_task_summary['event']]
            temp_result[dateStr][fieldName]=date_task_summary['totalcount']

    result = []
    for key in temp_result.keys():
        result.append({
            'date': key,
            'total_success': temp_result[key]['total_success'],
            'total_failed': temp_result[key]['total_failed'],
        })
    return result

rest_api_endpoint = "/astronomeranalytics/api/v1/"
# Creating a flask appbuilder BaseView
class AstronomerAnalytics(AppBuilderBaseView):
    default_view = "index" 

    @expose("/")
    def index(self):
            return self.render_template("/analytics-plugin/index.html",
                airflow_webserver_base_url=airflow_webserver_base_url,
                rest_api_endpoint=rest_api_endpoint,
                apis_metadata=apis_metadata,
            )        

    @expose("api/v1/tasks")
    def tasks(self):
      def try_reporter(r):
        try:
            return {r.__name__: r()}
        except Exception as e:
            logging.exception(f"Failed reporting {r.__name__}")
            return {r.__name__: str(e)}
      dags = try_reporter(dags_report) 
      return  { f"dags": format_db_response(dags) }

v_appbuilder_view = AstronomerAnalytics()
v_appbuilder_package = {
    "name": "API's",
    "category": "AstronomerAnalytics",
    "view": v_appbuilder_view,
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
            "view": v_appbuilder_view,
        },
    ]
    appbuilder_menu_items = []
    global_operator_extra_links = []
    operator_extra_links = []

