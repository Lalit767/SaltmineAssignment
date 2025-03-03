from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from scripts.ingestion_s3 import upload_json_files  # Import the function from the script

# AWS S3 Configuration
S3_BUCKET = "dataingestionjson"
S3_BASE_FOLDER = "product_metadata/"
S3_EVENTS_FOLDER = "users_events/"
LOCAL_METADATA_FOLDER = "/opt/airflow/datafiles/product_metadata"
LOCAL_EVENTS_FOLDER = "/opt/airflow/datafiles/events"

# Define Airflow DAG default arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 24),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# DAG definition
with DAG(
    "json_ingestion_s3_partitioned",
    default_args=default_args,
    schedule_interval="0 0 * * *",  # Runs daily at midnight
    catchup=False,
) as dag:

    upload_metadata_task = PythonOperator(
        task_id="upload_product_metadata",
        python_callable=upload_json_files,
        op_kwargs={
            "local_folder": LOCAL_METADATA_FOLDER,
            "s3_folder": S3_BASE_FOLDER,
            "ds": "{{ ds }}",
        },
    )

    upload_events_task = PythonOperator(
        task_id="upload_events",
        python_callable=upload_json_files,
        op_kwargs={
            "local_folder": LOCAL_EVENTS_FOLDER,
            "s3_folder": S3_EVENTS_FOLDER,
            "ds": "{{ ds }}",
        },
    )

    upload_events_task >> upload_metadata_task  # Ensures events upload first
