# import boto3

# def copy_s3_files(source_folder, destination_folder, execution_date):
#     s3 = boto3.client("s3")
    
#     source_bucket = source_folder.split("/")[2]
#     source_prefix = f"{'/'.join(source_folder.split('/')[3:])}{execution_date}/"  # Source partition
    
#     destination_bucket = destination_folder.split("/")[2]
#     destination_prefix = f"{'/'.join(destination_folder.split('/')[3:])}{execution_date}/"  # Destination partition
    
#     # List files in the partitioned source folder
#     response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)
    
#     if "Contents" in response:
#         for obj in response["Contents"]:
#             source_key = obj["Key"]  # Full S3 path of file
            
#             file_name = source_key.split("/")[-1]  # Extract file name
            
#             destination_key = f"{destination_prefix}{file_name}"  # Maintain date-partitioned structure
            
#             copy_source = {"Bucket": source_bucket, "Key": source_key}
#             s3.copy_object(Bucket=destination_bucket, CopySource=copy_source, Key=destination_key)
#             print(f"Copied {source_key} to {destination_key}")
#     else:
#         print(f"No files found in source folder for {execution_date}.")

import boto3

def copy_s3_files(source_folder, destination_folder, **kwargs):
    s3 = boto3.client("s3")
    
    # Extract bucket and prefix from source
    source_bucket = source_folder.split("//")[1].split("/")[0]
    source_prefix = "/".join(source_folder.split("//")[1].split("/")[1:])  # Remove 's3://<bucket>/'

    # Extract bucket and prefix from destination
    destination_bucket = destination_folder.split("//")[1].split("/")[0]
    destination_prefix = "/".join(destination_folder.split("//")[1].split("/")[1:])

    # List all objects under source folder to find latest partition
    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix, Delimiter='/')

    partition_folders = [content['Prefix'] for content in response.get('CommonPrefixes', [])]
    
    if not partition_folders:
        print(f"No partition folders found in {source_folder}")
        return
    
    # Sort to get the latest partition folder
    latest_partition_folder = sorted(partition_folders)[-1]  # Latest date folder

    print(f"Latest partition folder: {latest_partition_folder}")
    
    # List all objects in the latest partition folder
    objects = s3.list_objects_v2(Bucket=source_bucket, Prefix=latest_partition_folder).get("Contents", [])
    
    for obj in objects:
        source_key = obj["Key"]
        destination_key = source_key.replace(source_prefix, destination_prefix, 1)

        print(f"Copying {source_key} to {destination_key}")
        
        s3.copy_object(
            Bucket=destination_bucket,
            CopySource={'Bucket': source_bucket, 'Key': source_key},
            Key=destination_key
        )

    print("File copy completed successfully!")
