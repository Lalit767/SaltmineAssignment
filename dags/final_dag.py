from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 3, 4),
    'catchup': False,
}

with DAG('sequential_dag', default_args=default_args, schedule_interval=None) as dag:
    trigger_dag1 = TriggerDagRunOperator(
        task_id='trigger_dag1',
        trigger_dag_id='json_ingestion_s3_partitioned',  # First DAG
        wait_for_completion=True
    )

    trigger_dag2 = TriggerDagRunOperator(
        task_id='trigger_dag2',
        trigger_dag_id='s3_to_redshift_transformed',  # Second DAG
        wait_for_completion=True
    )

    trigger_dag3 = TriggerDagRunOperator(
        task_id='trigger_dag3',
        trigger_dag_id='redshift_to_s3_dag',  # Third DAG
        wait_for_completion=True
    )

    trigger_dag1 >> trigger_dag2 >> trigger_dag3  # Ensure sequential execution
