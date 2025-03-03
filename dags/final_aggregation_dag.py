# from airflow import DAG
# from airflow.operators.python import PythonOperator
# from airflow.utils.dates import days_ago
# import psycopg2
# import pandas as pd
# import os
# import boto3

# # Redshift connection details
# REDSHIFT_HOST = "exi"
# REDSHIFT_PORT = "5439"
# REDSHIFT_DB = "dev"
# REDSHIFT_USER = "admin"
# REDSHIFT_PASSWORD = "Lalit123$"

# S3_BUCKET = "finalresultsevents"
# S3_PREFIX = "final_metrics_result/"


# # Connect to Redshift
# def get_redshift_connection():
#     conn = psycopg2.connect(
#         host=REDSHIFT_HOST,
#         port=REDSHIFT_PORT,
#         dbname=REDSHIFT_DB,
#         user=REDSHIFT_USER,
#         password=REDSHIFT_PASSWORD
#     )
#     return conn

# # Queries
# queries = {
#     "total_revenue_by_category": """
#         SELECT product_id, SUM(amount) AS total_revenue
#         FROM transformed.transformed_processed
#         GROUP BY product_id
#         ORDER BY total_revenue DESC;
#     """
#     # ,
#     # "top_3_most_viewed_products": """
#     #     SELECT product_id, views
#     #     FROM transformed.transformed_processed
#     #     where event_type="page_view"
#     #     ORDER BY views DESC
#     #     LIMIT 3;
#     # """,
#     # "repeat_buyers": """
#     #     WITH user_daily_purchases AS (
#     #         SELECT 
#     #             user_id,
#     #             DATE(purchase_timestamp) AS purchase_date,
#     #             COUNT(*) AS purchase_count
#     #         FROM transformed.transformed_processed
#     #         GROUP BY user_id, DATE(purchase_timestamp)
#     #     )
#     #     SELECT user_id, purchase_date, purchase_count
#     #     FROM user_daily_purchases
#     #     WHERE purchase_count > 1
#     #     ORDER BY purchase_count DESC;
#     # """
# }

# # Execute query function
# def execute_query(**kwargs):
#     query = kwargs['query']
#     conn = get_redshift_connection()
#     df = None
#     try:
#         with conn.cursor() as cursor:
#             cursor.execute(query)
#             colnames = [desc[0] for desc in cursor.description]
#             rows = cursor.fetchall()
#             df = pd.DataFrame(rows, columns=colnames)
#             print(df)
#     except Exception as e:
#         print(f"Error executing query: {e}")
#     finally:
#         conn.close()
#     return df

# # Define DAG
# default_args = {
#     'owner': 'airflow',
#     'start_date': days_ago(1),
#     'retries': 1,
# }

# dag = DAG(
#     dag_id='redshift_query_dag',
#     default_args=default_args,
#     schedule_interval='@daily',
#     catchup=False
# )

# # Upload to S3 function
# def upload_to_s3(**kwargs):
#     s3 = boto3.client('s3')
#     ti = kwargs['ti']
    
#     for query_name in queries.keys():
#         file_path = ti.xcom_pull(key=query_name)
#         if file_path:
#             s3_key = f"{S3_PREFIX}{query_name}.csv"
#             s3.upload_file(file_path, S3_BUCKET, s3_key)
#             print(f"Uploaded {file_path} to s3://{S3_BUCKET}/{s3_key}")

# # Define tasks
# tasks = []
# for key, query in queries.items():
#     task = PythonOperator(
#         task_id=f"execute_{key}",
#         python_callable=execute_query,
#         op_kwargs={'query': query},
#         dag=dag,
#     )
#     tasks.append(task)
# upload_task = PythonOperator(
#     task_id="upload_to_s3",
#     python_callable=upload_to_s3,
#     provide_context=True,
#     dag=dag,
# )

# # Set task dependencies
# tasks[0] >> upload_task
# # >> tasks[1] >> tasks[2]

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from scripts.final_aggregation import execute_query, upload_to_s3, queries

# Define DAG arguments
default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "retries": 1,
}

dag = DAG(
    dag_id="redshift_to_s3_dag",
    default_args=default_args,
    schedule_interval=""0 3 * * *"",
    catchup=False
)

# Define tasks
def query_and_store(**kwargs):
    """Executes query and pushes file path to XCom."""
    query_name = kwargs["query_name"]
    query = queries[query_name]
    file_path = execute_query(query_name, query)
    
    if file_path:
        kwargs["ti"].xcom_push(key=query_name, value=file_path)

def upload_results(**kwargs):
    """Pulls file path from XCom and uploads to S3."""
    ti = kwargs["ti"]
    
    for query_name in queries.keys():
        file_path = ti.xcom_pull(task_ids=f"execute_{query_name}", key=query_name)
        if file_path:
            upload_to_s3(file_path, query_name)

# Create tasks dynamically
query_tasks = []
for query_name in queries.keys():
    task = PythonOperator(
        task_id=f"execute_{query_name}",
        python_callable=query_and_store,
        op_kwargs={"query_name": query_name},
        dag=dag
    )
    query_tasks.append(task)

# Upload task
upload_task = PythonOperator(
    task_id="upload_to_s3",
    python_callable=upload_results,
    provide_context=True,
    dag=dag,
)

# Set dependencies
for task in query_tasks:
    task >> upload_task

