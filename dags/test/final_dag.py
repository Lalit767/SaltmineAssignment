from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 3, 4),
    'retries': 1,
    'email_on_failure': True,  # Will only work if SMTP is configured in Airflow
    'email': ['lalit.anand676@gmail.com'],  # Ensure Airflow SMTP settings are configured
}

with DAG(
        "sequential_dag", 
        default_args=default_args, 
        schedule="0 1 * * *",  # Runs daily at 1 AM
        catchup=False,  # Prevents running past DAG executions
    ) as dag:

    trigger_dag1 = TriggerDagRunOperator(
        task_id='trigger_dag1',
        trigger_dag_id='json_ingestion_s3_partitioned',  # Ingestion DAG
        wait_for_completion=True
    )

    trigger_dag2 = TriggerDagRunOperator(
        task_id='trigger_dag2',
        trigger_dag_id='s3_to_redshift_transformed',  # Transformation DAG
        wait_for_completion=True
    )

    trigger_dag3 = TriggerDagRunOperator(
        task_id='trigger_dag3',
        trigger_dag_id='redshift_to_s3_dag',  # Final Aggregation DAG
        wait_for_completion=True
    )

    trigger_dag1 >> trigger_dag2 >> trigger_dag3  # Ensure sequential execution
