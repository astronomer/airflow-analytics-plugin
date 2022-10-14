# Airflow Plugin #

This is an [Airflow plugin](https://airflow.apache.org/docs/apache-airflow/stable/plugins.html) that directly queries the Airflow metadata database and returns certain analytics at an HTTP endpoint.

This plugin is installed by default in the astro-runtime images starting with 6.1.0-alpha4. It should not need to be manually installed by users.

## How do I test this repo

You must have the astro CLI installed.

1. Clone repo
2. Run `astro dev init`
3. Create a `plugins/astronomer_analytics_plugin` directory in your local Airflow instance
3. Copy the `analytics_plugin.py` file in this project directory into the new `plugins/astronomer_analytics_plugin` directory of your local Airflow instance
4. Run `astro dev start`
5. Login to the local Airflow webserver at `http://localhost:8080` with the username and password provided.
   If the "Astronomer Analytics" tab is visible at the top of the page, this plugin is installed.
6. To get the total numbers of successful and failed tasks, initiate an HTTP request `http://localhost:8080/astronomeranalytics/v1/tasks?startDate=2022-08-01&endDate=2022-08-30` with optional URL query parameters startDate and endDate.

   Example response:
   ```json
   {
       "tasks": {
           "total_failed": 25841090,
           "total_success": 12826442
       }
   }
   ```

## Publishing new packages to GitHub

1. Update the `__version__` variable in `analytics_plugin.py` file
2. Run `python -m build`
3. Upload the generated Wheel (`.whl`) file generated in the dist folder to GitHub as a release
