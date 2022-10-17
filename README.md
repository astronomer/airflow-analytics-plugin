# Plugin used to get analytics from deployments for software platform (gen1) 

## in plugins directory you can find file "astro-analytics"
Which finds a db session using how telescope does it and then has a function to query the db directly for the information we want.   
Airflow allows you to make plugins by simply dropping them in the plugins repo and using `AirflowPlugin` class with all the required fields:  
https://airflow.apache.org/docs/apache-airflow/stable/plugins.html 

## How do I test this repo
you must have the astro cli installed

1. clone repo
2. run `astro dev init`
3. copy files in plugins directory into plugins directory that was created when you run astro dev init
4. run `astro dev start` 
5. check the astro ui based on what command like tells you 
```
Example: 
Project is running! All components are now available.
Airflow Webserver: http://localhost:8080
Postgres Database: localhost:5432/postgres
```
login with provided username/pass
Look at the bar at the top and find "AstronomerAnalytics" 
That means its working

4. Do HTTP request

Do a HTTP get request `http://localhost:8080/astronomeranalytics/v1/tasks?startDate=2022-08-01&endDate=2022-08-30`  
with params startDate and endDate with the format  
YYYY-MM-DD   
Will retrieve dag data from the specified dates  


Example response
```JSON
{
    "dags": {
        "total_failed": 25841090,
        "total_success": 12826442
    }
}
```

based on https://github.com/teamclairvoyant/airflow-rest-api-plugin and telescope repo

## How do I publish to github

1. Update the version in the setup.py file 
2. Run python -m build
3. upload the .whl file generated in the dist folder to github as a release
