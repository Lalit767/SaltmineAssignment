import boto3
import pandas as pd
import json
import io
from datetime import datetime

# S3 Configuration
s3_bucket = "dataingestionjson"
s3_prefix = "users_events/"  # Folder path inside S3 bucket
s3_prefix1 = "product_metadata/"  # Folder path inside S3 bucket
output_path = "processed/"  # Output path in S3

s3_client = boto3.client("s3")

def get_latest_partition(bucket, prefix):
    """Retrieve the latest partition folder from S3"""
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")

    partitions = []
    for obj in response.get("CommonPrefixes", []):
        partition = obj["Prefix"].rstrip("/").split("/")[-1]
        if partition.replace("-", "").isdigit():  # Ensures it's a date-like partition
            partitions.append(partition)

    if not partitions:
        raise ValueError(f"No partitions found under s3://{bucket}/{prefix}")

    return max(partitions)

latest_partition = get_latest_partition(s3_bucket, s3_prefix)
print(f"Latest partition lalit: {latest_partition}")

# Get latest partitions
latest_ingestion_date = get_latest_partition(s3_bucket, s3_prefix)
s3_ingestion_path = f"{s3_prefix}{latest_ingestion_date}/"
print(s3_ingestion_path)
s3_ingestion_path1 = f"{s3_prefix1}{latest_ingestion_date}/"
print(s3_ingestion_path1)
s3_path = f"s3://{s3_bucket}/{output_path}{latest_partition}/transformed_data.parquet"
print(f"S3 Path: {s3_path}")
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

# Read user events & product metadata
user_events_df = read_json_from_s3(s3_bucket, s3_ingestion_path)
print(user_events_df)
product_metadata_df = read_json_from_s3(s3_bucket, s3_ingestion_path1)
print(product_metadata_df)

# Data Cleaning
user_events_df.dropna(subset=["event_details.user.user_id", "event_details.product.product_id", "event_details.timestamp"], inplace=True)
print("Latest partition Megha1:",user_events_df)
product_metadata_df.dropna(subset=["user_id", "product_id"], inplace=True)
user_events_df["event_details.product.amount"] = user_events_df["event_details.product.amount"].astype(float).fillna(0)
product_metadata_df["amount"] = product_metadata_df["amount"].astype(float).fillna(0)
product_metadata_df["stock"] = product_metadata_df["stock"].astype(float).fillna(0)
user_events_df["timestamp"] = pd.to_datetime(user_events_df["event_details.timestamp"], errors="coerce")

# renaming product_id column of user_events_df
user_events_df.rename(columns={"event_details.product.product_id": "product_id"}, inplace=True)
print("Latest partition lalit1:",user_events_df)
print("Latest partition lalit2:",product_metadata_df)
# Enrichment
enriched_df = user_events_df.merge(product_metadata_df, on="product_id", how="left")

print("Latest partition lalit3:",enriched_df)


# Transformation
enriched_df["amount"] = enriched_df["amount"].round(2)
# renaming product_id column of user_events_df
enriched_df.rename(columns={"timestamp_x": "Timestamp"}, inplace=True)
enriched_df["Timestamp"] = pd.to_datetime(enriched_df["Timestamp"], errors="coerce")
enriched_df["partition_date"] = enriched_df["Timestamp"].dt.strftime("%Y-%m-%d")
print("Latest partition lalit4:",enriched_df)

# Convert to Parquet
output_buffer = io.BytesIO()
enriched_df.to_parquet(output_buffer, index=False)
output_buffer.seek(0)

# Upload to S3
output_key = f"{output_path}{latest_ingestion_date}/transformed_data.txt"
print("Latest partition lalit5:",output_key)
s3_client.put_object(Bucket=s3_bucket, Key=output_key, Body=output_buffer.getvalue())

print(f"Data processing complete. File uploaded to s3://{s3_bucket}/{output_key}")
