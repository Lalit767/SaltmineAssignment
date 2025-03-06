from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from scripts.ingestion_s3 import upload_json_files  # Import function
from scripts.cleanUp_local_files import remove_files_from_folders  # Import function
from scripts.s3_operations import copy_s3_files
# AWS S3 Configuration
S3_BUCKET = "dataingestionraw"
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
    "email": ['lalit.anand676@gmail.com'],
    "email_on_success": True,
    "email_on_failure": True,
    "email_on_retry": True,
    "retry_delay": timedelta(minutes=5),
}

# DAG definition
with DAG(
    "final_dag",
    default_args=default_args,
    schedule_interval="* * * * *",  # Manually triggered or use "0 1 * * *" for daily 1 AM UTC
    catchup=False,
    max_active_runs=1,
) as dag:

    # File Sensor to wait for product metadata file
    wait_for_metadata_file = FileSensor(
        task_id="wait_for_metadata_file",
        filepath="*.json",
        fs_conn_id="fs_default_1",
        poke_interval=60,  # Check every 60 seconds
        timeout=600,  # Fail after 10 minutes
        mode="poke",
    )

    # File Sensor to wait for events file
    wait_for_events_file = FileSensor(
        task_id="wait_for_events_file",
        filepath="*.json",
        fs_conn_id="fs_default",
        poke_interval=60,  # Check every 60 seconds
        timeout=600,  # Fail after 10 minutes
        mode="poke",
    )

    # Upload product metadata
    upload_metadata_task = PythonOperator(
        task_id="upload_product_metadata",
        python_callable=upload_json_files,
        op_kwargs={
            "local_folder": LOCAL_METADATA_FOLDER,
            "s3_folder": S3_BASE_FOLDER,
            "ds": "{{ ds }}",
        },
    )

    # Upload events
    upload_events_task = PythonOperator(
        task_id="upload_events",
        python_callable=upload_json_files,
        op_kwargs={
            "local_folder": LOCAL_EVENTS_FOLDER,
            "s3_folder": S3_EVENTS_FOLDER,
            "ds": "{{ ds }}",
        },
    )

    # Cleanup task
    cleanup_task = PythonOperator(
    task_id="cleanup_local_files",
    python_callable=remove_files_from_folders,
    op_kwargs={"folders": [LOCAL_METADATA_FOLDER, LOCAL_EVENTS_FOLDER]},
    dag=dag
    )

    # Trigger Transformation DAG
    trigger_transformation_dag = TriggerDagRunOperator(
        task_id="trigger_transformation_dag",
        trigger_dag_id="s3_to_redshift_transformed",  # Ensure this DAG exists
        wait_for_completion=True,
    )

    # Trigger Aggregation DAG
    trigger_final_aggregation_dag = TriggerDagRunOperator(
        task_id="trigger_final_aggregation_dag",
        trigger_dag_id="redshift_to_s3_dag",  # Ensure this DAG exists
        wait_for_completion=True,
    )

    # Final task: Copy files from source S3 folder to audit S3 folder
    copy_product_metadata_to_audit_task = PythonOperator(
        task_id="copy_product_metadata_to_audit",
        python_callable=copy_s3_files,
        op_kwargs={
            "source_folder": "s3://dataingestionraw/product_metadata/",
            "destination_folder": "s3://dataingestionaudit/product_metadata/",
        },
    )

    copy_events_to_audit_task = PythonOperator(
        task_id="copy_events_to_audit",
        python_callable=copy_s3_files,
        op_kwargs={
            "source_folder": "s3://dataingestionraw/events/",
            "destination_folder": "s3://dataingestionaudit/events/",
        },
    )

    # Define task dependencies
    wait_for_metadata_file >> upload_metadata_task
    wait_for_events_file >> upload_events_task
    [upload_metadata_task, upload_events_task] >> cleanup_task  # Cleanup happens after uploads
    cleanup_task >> trigger_transformation_dag
    trigger_transformation_dag >> trigger_final_aggregation_dag
    trigger_final_aggregation_dag >> copy_product_metadata_to_audit_task
    copy_product_metadata_to_audit_task >> copy_events_to_audit_task
