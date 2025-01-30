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

    # Optionally, make it public (or you could generate signed URLs)
    # blob.make_public()  
    # print("File uploaded and made public")

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
    If the blob is set to public, users can directly access it via this URL.
    """
    return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
