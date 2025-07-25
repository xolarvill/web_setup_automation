# web_app.py
import uvicorn
import webbrowser
from threading import Timer
from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any
import os

# --- Basic Setup ---
# Create the FastAPI application
app = FastAPI(
    title="Web Setup Automation API",
    description="API server for the web-based UI.",
    version="1.0.0"
)

# Get the absolute path to the directory containing this script
# This is crucial for PyInstaller to find the files when bundled
base_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(base_dir, "web", "static")

# Mount the 'static' directory to serve CSS, JS, and other static files
# The path "/static" in the URL will correspond to the "web/static" folder
app.mount("/static", StaticFiles(directory=static_path), name="static")


# --- Frontend Serving ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serve the main index.html file.
    
    This is the entry point for the user's browser.
    """
    index_html_path = os.path.join(static_path, "index.html")
    try:
        with open(index_html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)


# --- API Endpoints ---
@app.post("/api/upload-folder")
async def api_upload_folder(files: List[UploadFile] = File(...)):
    """
    API endpoint to handle folder uploads.
    
    The frontend will send all files from the selected folder here.
    This is a placeholder and should be connected to your `upload_boto` or `upload_selenium` logic.
    """
    if not files:
        return JSONResponse(status_code=400, content={"message": "No files received."})

    # Example: Just count the files and list their names
    file_count = len(files)
    file_names = [file.filename for file in files]
    
    print(f"Received {file_count} files.")
    # Here you would trigger your actual upload logic
    # e.g., for file in files: await upload_boto.process(file)

    return {
        "message": f"Successfully received {file_count} files for upload.",
        "filenames": file_names
    }

@app.post("/api/generate-json")
async def api_generate_json(config_data: Dict[str, Any] = Body(...)):
    """
    API endpoint to generate the JSON configuration.
    
    The frontend will send the state of all input fields in the request body.
    This should be connected to your JSON generation logic.
    """
    print("Received data for JSON generation:", config_data)
    
    # Here you would call your existing JSON generation functions
    # e.g., generated_json = your_json_generator(config_data)
    
    # Placeholder response
    generated_json = {
        "status": "success",
        "message": "JSON would be generated here.",
        "received_config": config_data
    }
    
    return JSONResponse(content=generated_json)


# --- Server Launcher ---
def open_browser():
    """
    Opens the default web browser to the application's URL.
    """
    try:
        webbrowser.open_new("http://127.0.0.1:8000")
    except Exception as e:
        print(f"Could not open browser: {e}")

if __name__ == "__main__":
    """
    This block runs the Uvicorn server when the script is executed directly.
    It's configured for local development.
    """
    print("Starting the Web Setup Automation server...")
    print("Access the UI at http://127.0.0.1:8000")
    
    # Start the browser automatically after a short delay
    Timer(1.5, open_browser).start()
    
    # Run the server
    uvicorn.run(
        "web_app:app",
        host="127.0.0.1",
        port=8000,
        reload=True, # reload=True is great for development, automatically restarts on code changes
        log_level="info"
    )
