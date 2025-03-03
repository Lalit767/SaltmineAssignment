import psycopg2
import pandas as pd
import boto3
import os
from datetime import datetime

# Redshift connection details
REDSHIFT_HOST = os.getenv("REDSHIFT_HOST")
REDSHIFT_PORT = os.getenv("REDSHIFT_PORT")
REDSHIFT_DB = os.getenv("REDSHIFT_DB")
REDSHIFT_USER = os.getenv("REDSHIFT_USER")
REDSHIFT_PASSWORD = os.getenv("REDSHIFT_PASSWORD")


# Get today's date for partitioning
PARTITION_DATE = datetime.now().strftime("%Y-%m-%d")

# S3 details
S3_BUCKET = "finalresultsevents"
S3_PREFIX = "final_metrics_result/"

# Queries
queries = {
    "total_revenue_by_category": """
        SELECT product_id, SUM(amount) AS total_revenue
        FROM transformed.transformed_processed
        GROUP BY product_id
        ORDER BY total_revenue DESC;
    """
        ,
     "top_3_most_viewed_products": """
         SELECT product_id, COUNT(*) AS view_count
         FROM transformed.transformed_processed
         WHERE event_type = 'page_view'
         GROUP BY product_id
         ORDER BY view_count DESC
         LIMIT 3;
     """
     ,
    "repeat_buyers": """
        SELECT user_id, 
        DATE(TIMESTAMP 'epoch' + timestamp / 1000000000 * INTERVAL '1 second') AS purchase_date,
        COUNT(*) AS purchase_count
        from transformed.transformed_processed
        WHERE event_type = 'purchase'
        GROUP BY user_id, DATE(TIMESTAMP 'epoch' + timestamp / 1000000000 * INTERVAL '1 second')
        HAVING COUNT(*) > 1
        ORDER BY purchase_count DESC;
     """
}

def get_redshift_connection():
    """Establishes a connection to Redshift."""
    conn = psycopg2.connect(
        host=REDSHIFT_HOST,
        port=REDSHIFT_PORT,
        dbname=REDSHIFT_DB,
        user=REDSHIFT_USER,
        password=REDSHIFT_PASSWORD
    )
    return conn

def execute_query(query_name, query):
    """Executes the given query and saves the result as a CSV file."""
    conn = get_redshift_connection()
    file_path = f"/tmp/{query_name}.csv"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            colnames = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=colnames)
            df.to_csv(file_path, index=False)
            print(f"Query {query_name} executed. Results saved to {file_path}")
            return file_path
    except Exception as e:
        print(f"Error executing query {query_name}: {e}")
    finally:
        conn.close()
    return None

def upload_to_s3(file_path, query_name):
    """Uploads the given file to S3."""
    s3 = boto3.client("s3")
    s3_key = f"{S3_PREFIX}{PARTITION_DATE}/{query_name}.csv"
    
    try:
        s3.upload_file(file_path, S3_BUCKET, s3_key)
        print(f"Uploaded {file_path} to s3://{S3_BUCKET}/{s3_key}")
    except Exception as e:
        print(f"Error uploading {file_path} to S3: {e}")
