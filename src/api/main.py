from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from datetime import datetime
from collections import Counter

from src.core.file_finder import find_files
from src.core.file_processor import create_zip_package

app = FastAPI(
    title="SUNAT File Finder & Processor API",
    description="An API to find and process SUNAT files.",
    version="2.0.0"
)

# --- Models ---
class FindRequest(BaseModel):
    path: str

class ProcessRequest(BaseModel):
    search_path: str
    output_dir: str
    delete_originals: bool = False

# --- Endpoints ---

@app.post("/find", summary="Find and list SUNAT files")
def find_endpoint(request: FindRequest):
    """
    Searches for SUNAT-compliant filenames in the provided directory path.

    - **path**: The absolute directory path to search in recursively.
    """
    search_path = request.path
    if not os.path.isabs(search_path) or not os.path.isdir(search_path):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or non-existent path: {search_path}"
        )

    try:
        found_files = find_files(search_path)
        return {
            "search_path": search_path,
            "files_found": len(found_files),
            "files": found_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process", summary="Find files and package them into a ZIP")
def process_endpoint(request: ProcessRequest):
    """
    Finds all SUNAT files in a directory, packages them into a single ZIP file,
    and optionally deletes the original source files.

    - **search_path**: The absolute directory path to search in.
    - **output_dir**: The absolute directory path to save the output ZIP file.
    - **delete_originals**: Set to true to delete the original files/containers.
    """
    search_path = request.search_path
    output_dir = request.output_dir

    if not os.path.isabs(search_path) or not os.path.isdir(search_path):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or non-existent search path: {search_path}"
        )
    if not os.path.isabs(output_dir) or not os.path.isdir(output_dir):
        raise HTTPException(
            status_code=400,
            detail=f"Output directory must be an absolute and existing path: {output_dir}"
        )

    try:
        # Step 1: Find files
        all_found_files = find_files(search_path)
        
        if not all_found_files:
            return {"message": "No files found in scan.", "files_found": 0}

        # Step 2: Prepare files for packaging and deletion
        files_to_package = []
        physical_files_to_delete = set()
        for file_info in all_found_files:
            if file_info.get('status') == 'UNICO':
                files_to_package.append(file_info)
            
            base_path = file_info['path'].split(':')[0]
            physical_files_to_delete.add(base_path)

        if not files_to_package:
            return {"message": "No unique files found to package.", "unique_files_packaged": 0}

        # Step 3: Calculate statistics
        total_unique_packaged = len(files_to_package)
        classifications_packaged = [f.get('classification', 'unknown') for f in files_to_package]
        stats_packaged = Counter(classifications_packaged)

        # Step 4: Generate filenames and paths
        log_dir = 'logs'
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"consolidado_{timestamp}.zip"
        output_zip_path = os.path.join(output_dir, zip_filename)
        process_log_filename = f"process_{timestamp}.txt"
        process_log_filepath = os.path.join(log_dir, process_log_filename)

        # Step 5: Determine which files to delete
        files_for_deletion = physical_files_to_delete if request.delete_originals else set()

        # Step 6: Create ZIP package
        create_zip_package(files_to_package, files_for_deletion, output_zip_path, log_filepath=process_log_filepath)
        
        return {
            "message": "Processing complete.",
            "files_found_in_scan": len(all_found_files),
            "unique_files_packaged": total_unique_packaged,
            "classification_stats": stats_packaged,
            "output_zip_file": output_zip_path,
            "process_log_file": process_log_filepath
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")