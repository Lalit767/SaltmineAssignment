import boto3
import pandas as pd
import json
import io
import psycopg2
import os
import numpy as np
from datetime import datetime

# S3 Configuration
s3_bucket = "dataingestionjson"
s3_prefix = "users_events/"
s3_prefix1 = "product_metadata/"
output_path = "processed"

s3_client = boto3.client("s3")

def get_latest_partition(bucket, prefix):
    """Retrieve the latest partition folder from S3"""
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")
    
    partitions = [obj["Prefix"].rstrip("/").split("/")[-1] for obj in response.get("CommonPrefixes", [])]
    partitions = [p for p in partitions if p.replace("-", "").isdigit()]

    if not partitions:
        raise ValueError(f"No partitions found under s3://{bucket}/{prefix}")
    
    return max(partitions)



def read_json_from_s3(bucket, prefix):
    """Read all JSON files from an S3 folder into a Pandas DataFrame"""
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    files = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".json")]

    df_list = []
    for file in files:
        obj = s3_client.get_object(Bucket=bucket, Key=file)
        data = json.load(obj["Body"])
        df_list.append(pd.json_normalize(data))

    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

def process_and_load_data():
    # Get latest partitions
    latest_ingestion_date = get_latest_partition(s3_bucket, s3_prefix)
    s3_ingestion_path = f"{s3_prefix}{latest_ingestion_date}/"
    s3_ingestion_path1 = f"{s3_prefix1}{latest_ingestion_date}/"
    partitioned_output_path = f"{output_path}/{latest_ingestion_date}/transformed_data.parquet"
    s3_path = f"s3://{s3_bucket}/{partitioned_output_path}"

    # Read user events & product metadata
    user_events_df = read_json_from_s3(s3_bucket, s3_ingestion_path)
    product_metadata_df = read_json_from_s3(s3_bucket, s3_ingestion_path1)
    print(product_metadata_df)

    # Rename Events data columns
    user_events_df.rename(columns={
        "event_details.event_type": "event_type",
        "event_details.user.user_id": "user_id",
        "event_details.product.product_id": "product_id",
        "event_details.product.amount": "amount",
        "event_details.timestamp": "timestamp"
    }, inplace=True)
    print("Rename",user_events_df)

    # Data Cleaning
    user_events_df.dropna(subset=["event_type","user_id", "product_id", "timestamp"], inplace=True)
    product_metadata_df.dropna(subset=["user_id", "product_id"], inplace=True)
    user_events_df["amount"] = user_events_df["amount"].astype(float).fillna(0)
    user_events_df['stock'] = np.nan  # Add missing 'stock' column
    user_events_df["stock"] = user_events_df["stock"].fillna(0)
    product_metadata_df["amount"] = product_metadata_df["amount"].astype(float).fillna(0)
    product_metadata_df["stock"] = product_metadata_df["stock"].fillna(0)
    user_events_df["timestamp"] = pd.to_datetime(user_events_df["timestamp"], errors="coerce")
    print("New column",user_events_df)

    # Perform the union (concat)
    enriched_df = pd.concat([user_events_df, product_metadata_df], ignore_index=True)
    print(enriched_df)
 
    # Enrichment
    enriched_df["amount"] = enriched_df["amount"].round(2)
    enriched_df["timestamp"] = pd.to_datetime(enriched_df["timestamp"], errors="coerce")
 #   enriched_df["partition_date"] = enriched_df["Timestamp"].dt.strftime("%Y-%m-%d")
    print("Enrichment",enriched_df)


    # Remove duplicates based on user_id, product_id, and Timestamp
    enriched_df.drop_duplicates(subset=["user_id", "product_id", "timestamp"], keep="last", inplace=True)
    print("Remove duplicates",enriched_df)


    # Load data into Redshift
    redshift_host = os.getenv("REDSHIFT_HOST")
    redshift_port = os.getenv("REDSHIFT_PORT")
    redshift_db = os.getenv("REDSHIFT_DB")
    redshift_user = os.getenv("REDSHIFT_USER")
    redshift_password = os.getenv("REDSHIFT_PASSWORD")
    redshift_table = os.getenv("REDSHIFT_TABLE")
    redshift_iam_role = os.getenv("REDSHIFT_IAM_ROLE")

    conn = psycopg2.connect(
        dbname=redshift_db,
        user=redshift_user,
        password=redshift_password,
        host=redshift_host,
        port=redshift_port
    )
    cursor = conn.cursor()

    # Function to Fetch existing data from Redshift
    def fetch_existing_data_from_redshift(conn, redshift_table):
        """Fetch existing records from Redshift for deduplication"""
        query = f"""
            SELECT event_type, user_id, product_id, amount, TIMESTAMP 'epoch' + timestamp / 1000000000 * INTERVAL '1 second' AS timestamp, stock
            FROM {redshift_table};

        """
        return pd.read_sql(query, conn)
    
    # Fetch existing data from Redshift
    existing_data = fetch_existing_data_from_redshift(conn, redshift_table)
    print("Existing",existing_data)


    # Convert to timezone-naive format (removes UTC) and all columns to lowercase
    enriched_df["timestamp"] = pd.to_datetime(enriched_df["timestamp"]).dt.tz_localize(None)
    existing_data["timestamp"] = pd.to_datetime(existing_data["timestamp"]).dt.tz_localize(None)


    if not existing_data.empty:
        # Merge and remove duplicates between Redshift & new data
        enriched_df = enriched_df.merge(
            existing_data, on=["user_id", "product_id", "timestamp"], how="left", indicator=True
        )
        enriched_df = enriched_df[enriched_df["_merge"] == "left_only"].drop(columns=["_merge"])
        
    if enriched_df.empty:
        print("No new data to load into Redshift. Skipping copy command.")
        return
    
     # Convert to Parquet
    output_buffer = io.BytesIO()
    enriched_df.to_parquet(output_buffer, index=False)
    output_buffer.seek(0)


    # Upload to S3
    s3_client.put_object(Bucket=s3_bucket, Key=partitioned_output_path, Body=output_buffer.getvalue())
    print(f"Processed data uploaded to {s3_path}")   


    # Read the Parquet file from S3
    file_path = "s3://dataingestionjson/processed/2025-03-03/transformed_data.parquet"
    df = pd.read_parquet(file_path)

    # Display column names
    print(df.columns)
    print(df)

    copy_query = f"""
        COPY {redshift_table}
        FROM '{s3_path}'
        IAM_ROLE '{redshift_iam_role}'
        FORMAT AS PARQUET;
    """

    cursor.execute(copy_query)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Data successfully loaded into Redshift table: {redshift_table}")

if __name__ == "__main__":
    process_and_load_data()


