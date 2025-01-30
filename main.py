# main.py
import os
import time
from flask import Flask, request, redirect, send_file, Response # type: ignore
from storage import get_list_of_files, upload_file, download_file, get_public_url

app = Flask(__name__)

# Replace this with the name of your bucket
# Example: "my-awesome-bucket"
BUCKET_NAME = os.environ.get("BUCKET_NAME", "my-flask-gcs-app-uploads")


@app.route("/", methods=["GET"])
def index():
    """
    Displays an HTML form for uploading images
    and lists the images currently in the GCS bucket.
    """
    html_form = """
    <h1>Image Uploader</h1>
    <form method="POST" action="/upload" enctype="multipart/form-data">
      <div>
        <label for="file">Choose a JPEG file to upload:</label>
        <input type="file" id="file" name="form_file" accept="image/jpeg" />
      </div>
      <div>
        <button type="submit">Upload</button>
      </div>
    </form>
    <hr>
    <h2>Existing Images</h2>
    <ul>
    """

    # Get list of files in the GCS bucket
    files = get_list_of_files(BUCKET_NAME)

    # Filter only JPEG or JPG
    image_files = [f for f in files if f.lower().endswith(".jpeg") or f.lower().endswith(".jpg")]

    for image in image_files:
        # Option 1: Serve from our own endpoint
        # link = f"/files/{image}"
        
        # Option 2: If publicly accessible, direct link to GCS
        # link = get_public_url(BUCKET_NAME, image)

        # For demonstration, we’ll serve from a Flask endpoint:
        link = f"/files/{image}"
        html_form += f"<li><a href='{link}' target='_blank'>{image}</a></li>"

    html_form += "</ul>"
    return html_form


@app.route("/upload", methods=["POST"])
def upload():
    """
    Receives the uploaded file from the user,
    saves it temporarily in /tmp, then uploads to GCS.
    """
    if "form_file" not in request.files:
        return "No file part in request", 400

    file = request.files["form_file"]
    if file.filename == "":
        return "No selected file", 400

    # Save to /tmp on Cloud Run
    tmp_path = os.path.join("/tmp", file.filename)
    file.save(tmp_path)

    # Upload to GCS
    upload_file(BUCKET_NAME, tmp_path, file.filename)

    # (Optional) remove local file if you want
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    return redirect("/")


@app.route("/files/<filename>", methods=["GET"])
def serve_file(filename):
    """
    Downloads the file from GCS into /tmp, then uses Flask's send_file to serve it.
    """
    # Download from GCS to /tmp
    local_path = os.path.join("/tmp", filename)
    download_file(BUCKET_NAME, filename, local_path)

    # The file is now in /tmp. We can serve it.
    # Because it’s an image, you can also do send_file(..., mimetype="image/jpeg")
    return send_file(local_path, mimetype="image/jpeg")


@app.route("/health")
def health():
    """
    A simple health endpoint to verify the app is up.
    """
    return "OK", 200


if __name__ == "__main__":
    # Only for local testing; Cloud Run will provide a production WSGI server.
    app.run(host="0.0.0.0", port=8080, debug=True)
