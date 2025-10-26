from flask import Flask, request, jsonify, render_template
from azure.storage.blob import BlobServiceClient, ContentSettings
from urllib.parse import quote
import os

app = Flask(__name__)

# Configuration (use environment variables in Azure)
CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.environ.get("AZURE_STORAGE_CONTAINER", "images-demo")

# Initialize Blob client
bsc = BlobServiceClient.from_connection_string(CONNECTION_STRING)
cc = bsc.get_container_client(CONTAINER_NAME)

# Explicitly store the container URL
CONTAINER_URL = cc.url.rstrip('/')  # e.g., "https://kaitlin.blob.core.windows.net/images-demo"


@app.route("/api/v1/upload", methods=["POST"])
def upload():
    """Upload a file to Azure Blob Storage with correct content type."""
    f = request.files["file"]
    blob_name = f.filename
    blob_client = cc.get_blob_client(blob_name)

    # Set correct content type based on file extension
    ext = os.path.splitext(blob_name)[1].lower()
    mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif"
    }.get(ext, "application/octet-stream")

    blob_client.upload_blob(f, overwrite=True,
                            content_settings=ContentSettings(content_type=mime_type))

    # Return the full URL
    url = f"{CONTAINER_URL}/{quote(blob_name)}"
    return jsonify(ok=True, url=url)


@app.route("/api/v1/gallery", methods=["GET"])
def gallery():
    """List all blobs in the container with proper URLs."""
    try:
        blob_list = cc.list_blobs()
        gallery_urls = [
            f"{CONTAINER_URL}/{quote(blob.name)}"
            for blob in blob_list
        ]
        return jsonify(ok=True, gallery=gallery_urls), 200
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.route("/api/v1/health", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return jsonify(status="healthy", container=CONTAINER_NAME)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # Only run locally; Azure uses gunicorn automatically
    app.run(debug=True, host="0.0.0.0", port=8000)
