import os
import glob

# Define local folder paths
LOCAL_FOLDERS = [
    "/opt/airflow/datafiles/product_metadata",
    "/opt/airflow/datafiles/events"
]
FILE_PATTERN = "*.json"  # Define file pattern to delete

def remove_files_from_folders(folders, file_pattern="*"):
    """Deletes files matching the pattern from multiple folders."""
    for folder_path in folders:
        files_to_remove = glob.glob(os.path.join(folder_path, file_pattern))
        
        if not files_to_remove:
            print(f"No files found in {folder_path} to delete.")
            continue

        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

if __name__ == "__main__":
    remove_files_from_folders(LOCAL_FOLDERS, FILE_PATTERN)
