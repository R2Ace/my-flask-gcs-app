# storage.py
from google.cloud import storage

# Create a single global Storage client,
# which can be reused across requests.
storage_client = storage.Client()

def get_list_of_files(bucket_name):
    """
    Lists all the blobs in the bucket.
    Returns a list of blob names (strings).
    """
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    files = []
    for blob in blobs:
        files.append(blob.name)
    return files

def upload_file(bucket_name, local_file_path, blob_name):
    """
    Uploads a local file to a bucket.
    local_file_path: path in local disk (/tmp/filename)
    blob_name: how the file will be named in the bucket
    """
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_file_path)
    # Not making the file public, as requested in requirements
    # print("File uploaded")

def upload_json(bucket_name, local_file_path, blob_name):
    """
    Uploads a JSON file to the bucket.
    Sets the content type to application/json.
    """
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_file_path, content_type='application/json')
    # Not making the file public, as requested in requirements
    # print("JSON file uploaded")

def download_file(bucket_name, blob_name, local_file_path):
    """
    Download a file from bucket into a local file path.
    """
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_file_path)
    return local_file_path

def get_public_url(bucket_name, blob_name):
    """
    Return the public URL for a blob in the bucket.
    NOTE: This function is kept for compatibility, but should not be used
    as per requirements to not leak direct bucket URLs.
    """
    return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"