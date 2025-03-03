from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.append("/opt/airflow/dags/scripts")  # Ensure Python can find your script
from scripts.S3_transformation_redshift import process_and_load_data



# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "s3_to_redshift_transformed",
    default_args=default_args,
    description="Pipeline to extract, transform, and load data from S3 to Redshift",
    schedule_interval=""0 2 * * *"",
    catchup=False,
)

# Task to run the logic script
run_etl_task = PythonOperator(
    task_id="run_etl_task",
    python_callable=process_and_load_data,
    dag=dag,
)

run_etl_task
