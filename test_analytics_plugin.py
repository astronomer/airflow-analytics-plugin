import os
import tempfile
from analytics_plugin import AstronomerAnalytics
from flask import Flask
from flask_appbuilder import AppBuilder, SQLA

def test_plugin_no_tasks_returned(mocker):
    with tempfile.TemporaryDirectory() as tmp_dir:
        app = Flask(__name__)
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f"sqlite:///{os.path.join(tmp_dir, 'src.db')}"
        app.config['SECRET_KEY'] = 'sekrit!'
        mocker.patch("analytics_plugin.tasks_report_query", return_value={})
        db = SQLA(app)
        appbuilder = AppBuilder(app, db.session)
        appbuilder.add_view(AstronomerAnalytics(), name='analytics')
        # Create a test client using the Flask application configured for testing
        with app.test_client() as test_client:
            response = test_client.get('/astronomeranalytics/api/v1/tasks?startDate=2022-08-01&endDate=2022-08-01')
            assert response.status_code == 200
            assert response.data == b'{"tasks":{}}\n'

def test_plugin_tasks_returned(mocker):
    with tempfile.TemporaryDirectory() as tmp_dir:
        app = Flask(__name__)
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f"sqlite:///{os.path.join(tmp_dir, 'src.db')}"
        app.config['SECRET_KEY'] = 'sekrit!'
        return_value={"success": 10, "failed": 20}
        mocker.patch("analytics_plugin.tasks_report_query", return_value=return_value)
        db = SQLA(app)
        appbuilder = AppBuilder(app, db.session)
        appbuilder.add_view(AstronomerAnalytics(), name='analytics')
        # Create a test client using the Flask application configured for testing
        with app.test_client() as test_client:
            response = test_client.get('/astronomeranalytics/api/v1/tasks?startDate=2022-08-01&endDate=2022-08-01')
            assert response.status_code == 200
            assert response.data == b'{"tasks":{"total_failed":20,"total_success":10}}\n'

def test_plugin_will_error_without_date_params(mocker):
    with tempfile.TemporaryDirectory() as tmp_dir:
        app = Flask(__name__)
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f"sqlite:///{os.path.join(tmp_dir, 'src.db')}"
        app.config['SECRET_KEY'] = 'sekrit!'
        mocker.patch("analytics_plugin.tasks_report_query", return_value={})
        db = SQLA(app)
        appbuilder = AppBuilder(app, db.session)
        appbuilder.add_view(AstronomerAnalytics(), name='analytics')
        # Create a test client using the Flask application configured for testing
        with app.test_client() as test_client:
            response = test_client.get('/astronomeranalytics/api/v1/tasks')
            assert response.status_code == 500

def test_plugin_bad_dates(mocker):
    with tempfile.TemporaryDirectory() as tmp_dir:
        app = Flask(__name__)
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f"sqlite:///{os.path.join(tmp_dir, 'src.db')}"
        app.config['SECRET_KEY'] = 'sekrit!'
        mocker.patch("analytics_plugin.tasks_report_query", return_value={})
        db = SQLA(app)
        appbuilder = AppBuilder(app, db.session)
        appbuilder.add_view(AstronomerAnalytics(), name='analytics')
        # Create a test client using the Flask application configured for testing
        with app.test_client() as test_client:
            response = test_client.get('/astronomeranalytics/api/v1/tasks?startDate=bad&endDate=dates')
            assert response.status_code == 500