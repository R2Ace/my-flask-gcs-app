# main.py
import os
import time
import json
import mimetypes
from flask import Flask, request, redirect, send_file, Response

from storage import get_list_of_files, upload_file, download_file, get_public_url, upload_json
from gemini_service import analyze_image

app = Flask(__name__)

# Bucket name
BUCKET_NAME = os.environ.get("BUCKET_NAME", "my-flask-gcs-app-uploads")

@app.route("/", methods=["GET"])
def index():
    """
    Displays an HTML form for uploading images and shows thumbnails.
    The background color is dynamically set from an environment variable.
    """
    # Read the background color from an environment variable; default to blue if not set
    bg_color = os.environ.get("BACKGROUND_COLOR", "blue")
    html_form = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Image Captioner</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
                background-color: {bg_color};
            }}
            h1 {{ color: #333; }}
            .upload-form {{
                margin-bottom: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }}
            .button {{
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
            /* Gallery styles */
            .image-gallery {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 20px; 
                margin-top: 20px;
            }}
            .image-card {{
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }}
            .image-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            .image-thumbnail {{
                width: 100%;
                height: 150px;
                object-fit: cover;
            }}
            .image-name {{
                padding: 10px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .image-card a {{
                text-decoration: none;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <h1>AI Image Captioner</h1>
        <div class="upload-form">
            <h2>Upload a New Image</h2>
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <div style="margin-bottom: 15px;">
                    <label for="file">Choose a JPEG image to upload:</label>
                    <input type="file" id="file" name="form_file" accept="image/jpeg" required />
                </div>
                <div>
                    <button type="submit" class="button">Upload & Generate Caption</button>
                </div>
            </form>
        </div>
        <h2>Uploaded Images</h2>
        <div class="image-gallery">
    """
    # Get list of files in the GCS bucket
    files = get_list_of_files(BUCKET_NAME)
    image_files = [f for f in files if f.lower().endswith((".jpeg", ".jpg"))]
    
    for image in image_files:
        view_link = f"/view/{image}"
        thumbnail_link = f"/files/{image}"
        html_form += f"""
            <div class="image-card">
                <a href="{view_link}">
                    <img src="{thumbnail_link}" alt="{image}" class="image-thumbnail">
                    <div class="image-name">{image}</div>
                </a>
            </div>
        """
    
    html_form += """
        </div>
    </body>
    </html>
    """
    return html_form

@app.route("/upload", methods=["POST"])
def upload():
    """
    Receives the uploaded file from the user,
    saves it temporarily in /tmp, then uploads to GCS.
    Also analyzes the image using Gemini AI API and saves the caption.
    """
    if "form_file" not in request.files:
        return "No file part in request", 400
    
    file = request.files["form_file"]
    if file.filename == "":
        return "No selected file", 400
    
    # Save to /tmp on Cloud Run
    tmp_path = os.path.join("/tmp", file.filename)
    file.save(tmp_path)
    
    # Upload image to GCS
    upload_file(BUCKET_NAME, tmp_path, file.filename)
    
    try:
        # Analyze image with Gemini AI API
        ai_response = analyze_image(tmp_path)
        
        # Create JSON file with the same base name
        base_name = os.path.splitext(file.filename)[0]
        json_file_name = f"{base_name}.json"
        json_tmp_path = os.path.join("/tmp", json_file_name)
        
        # Save JSON file locally
        with open(json_tmp_path, 'w') as f:
            json.dump(ai_response, f)
        
        # Upload JSON to GCS
        upload_json(BUCKET_NAME, json_tmp_path, json_file_name)
        
        # Clean up local files
        if os.path.exists(json_tmp_path):
            os.remove(json_tmp_path)
    except Exception as e:
        print(f"Error analyzing image: {e}")
        # Continue even if the AI analysis fails
    
    # Remove local image file
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    
    # Redirect back to the home page to show the gallery
    return redirect("/")

@app.route("/view/<filename>", methods=["GET"])
def view_image_with_caption(filename):
    """
    Shows the image with its caption in a nice formatted page.
    If the caption isn't available, it still shows the image.
    """
    # Get the image file
    image_local_path = os.path.join("/tmp", filename)
    download_file(BUCKET_NAME, filename, image_local_path)
    
    # Get the caption JSON if it exists
    base_name = os.path.splitext(filename)[0]
    json_file_name = f"{base_name}.json"
    json_local_path = os.path.join("/tmp", json_file_name)
    
    # Default caption values
    title = "Untitled Image"
    description = "No AI-generated description available for this image."
    
    try:
        # Check if JSON file exists in the bucket
        files = get_list_of_files(BUCKET_NAME)
        if json_file_name in files:
            # Download and read the JSON file
            download_file(BUCKET_NAME, json_file_name, json_local_path)
            with open(json_local_path, 'r') as f:
                caption_data = json.load(f)
                title = caption_data.get('title', title)
                description = caption_data.get('description', description)
            
            # Clean up the JSON file
            if os.path.exists(json_local_path):
                os.remove(json_local_path)
    except Exception as e:
        print(f"Error loading caption: {e}")
        # Continue even if the caption loading fails
    
    # Create a binary data URL to embed the image directly
    image_url = f"/files/{filename}"
    
    # Get background color for consistency with main page
    bg_color = os.environ.get("BACKGROUND_COLOR", "blue")
    
    # Generate the HTML response with the image and caption
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: {bg_color}; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; background-color: white; 
                         box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; margin-top: 0; padding-bottom: 15px; border-bottom: 1px solid #eee; }}
            img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; 
                  border: 1px solid #ddd; border-radius: 4px; }}
            .description {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; line-height: 1.6; }}
            .back-link {{ margin-top: 20px; display: inline-block; }}
            .back-link a {{ color: #0066cc; text-decoration: none; }}
            .back-link a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <img src="{image_url}" alt="{filename}" />
            <div class="description">
                <p>{description}</p>
            </div>
            <div class="back-link">
                <a href="/">← Back to image gallery</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Clean up the local image file
    if os.path.exists(image_local_path):
        os.remove(image_local_path)
    
    return html

@app.route("/files/<filename>", methods=["GET"])
def serve_file(filename):
    """
    Downloads the file from GCS into /tmp, then uses Flask's send_file to serve it.
    """
    # Download from GCS to /tmp
    local_path = os.path.join("/tmp", filename)
    download_file(BUCKET_NAME, filename, local_path)
    
    # Determine mimetype based on file extension
    mimetype, _ = mimetypes.guess_type(filename)
    if not mimetype and filename.lower().endswith(('.jpg', '.jpeg')):
        mimetype = "image/jpeg"
    
    # The file is now in /tmp. We can serve it.
    return send_file(local_path, mimetype=mimetype)

@app.route("/health")
def health():
    """
    A simple health endpoint to verify the app is up.
    """
    return "OK", 200

@app.route("/version")
def version():
    """
    Returns the background color being used.
    """
    bg_color = os.environ.get("BACKGROUND_COLOR", "blue")
    return f"Using {bg_color} background", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
