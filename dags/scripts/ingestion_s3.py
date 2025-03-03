from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import boto3

# # AWS S3 Configuration
S3_BUCKET = "dataingestionjson"

# Initialize S3 Client
s3_client = boto3.client("s3")

# Function to upload files to S3 with partitioned key
def upload_json_files(local_folder, s3_folder, ds, **kwargs):
    partition_path = f"{ds}/"  # Change to single-date format (YYYY-MM-DD)
    print(f"Partition Path: {partition_path}")

    for file_name in os.listdir(local_folder):
        if file_name.endswith(".json"):
            file_path = os.path.join(local_folder, file_name)
            s3_key = f"{s3_folder}{partition_path}{file_name}"
            print(f"Uploading {file_name} to {s3_key}")

            try:
                # Upload file to S3
                s3_client.upload_file(file_path, S3_BUCKET, s3_key)
                print(f"Uploaded: {file_name} to S3://{S3_BUCKET}/{s3_key}")

            except Exception as e:
                print(f"Error uploading {file_name}: {e}")

