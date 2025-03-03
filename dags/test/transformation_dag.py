from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 27),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def run_processing_script():
    subprocess.run(["python3", "/opt/airflow/dags/scripts/transformation.py"], check=True)

with DAG(
    "s3_data_transformation",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
) as dag:

    transform_data = PythonOperator(
        task_id="transform_s3_data",
        python_callable=run_processing_script,
    )

    transform_data
