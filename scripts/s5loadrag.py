import requests
import os
import glob
import json # Used only for potential error message parsing
import time # Added for timing

# --- Configuration ---
# Replace with your Open WebUI instance URL (e.g., "http://localhost:8080")
OPENWEBUI_BASE_URL = "http://llm:3000" 
# Replace with your generated Open WebUI API Key
OPENWEBUI_TOKEN = 'your_api_key_here' #this is a openwebui key
# Replace with the *ID* of the Knowledge Collection you want to add files to
# Find this ID in the OpenWebUI interface or via its API if available.
KNOWLEDGE_COLLECTION_ID = "2e53e76e-05d1-4cd4-9791-cf0310551b4e" 
# Folder containing the JSON files to upload (relative to the script location)
DATA_FOLDER_PATH = "jdata" 
# --- End Configuration ---

# Construct CORRECT API URLs based on user's latest feedback
# Upload endpoint: POST /api/v1/files/ (note the trailing slash)
upload_url = f"{OPENWEBUI_BASE_URL}/api/v1/files/"
# Add to knowledge collection endpoint: POST /api/v1/knowledge/{id}/file/add
collection_add_url = f"{OPENWEBUI_BASE_URL}/api/v1/knowledge/{KNOWLEDGE_COLLECTION_ID}/file/add"


# Prepare headers for authentication
headers_auth_only = {
    "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
    "Accept": "application/json" # Good practice
}

# Headers for adding to collection (requires Content-Type for JSON payload)
headers_json_payload = {
    "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def upload_file(file_path):
    """Uploads a single file using /api/v1/files/ and returns its ID."""
    file_name = os.path.basename(file_path)
    print(f"Attempting to upload: {file_name} using endpoint: {upload_url}")
    
    try:
        with open(file_path, 'rb') as f:
            # Assuming 'file' is still the correct field name for multipart/form-data
            files = {'file': (file_name, f, 'application/json')} 
            # Use headers with just auth for multipart upload
            response = requests.post(upload_url, headers=headers_auth_only, files=files, timeout=60) 
            response.raise_for_status() 

            response_data = response.json()
            # Assuming the response still contains a top-level 'id' field for the uploaded file
            if "id" in response_data:
                file_id = response_data["id"]
                print(f"  Success! Uploaded '{file_name}'. Received File ID: {file_id}")
                return file_id
            else:
                print(f"  Error: 'id' field not found directly in response for {file_name}.")
                print(f"  Full Response: {response_data}") 
                return None

    except requests.exceptions.RequestException as e:
        print(f"  Error uploading {file_name}: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"  Response Status Code: {e.response.status_code}")
             try:
                 error_details = e.response.json()
                 print(f"  API Error Details: {error_details}")
             except json.JSONDecodeError:
                 print(f"  Response Text (non-JSON): {e.response.text[:500]}...")
        else:
             print("  No response received from server.")
        return None
    except FileNotFoundError:
        print(f"  Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"  An unexpected error occurred during upload of {file_path}: {e}")
        return None


def add_file_to_knowledge_collection(file_id, file_name):
    """Adds an uploaded file (by ID) to the specified knowledge collection using /api/v1/knowledge/{id}/file/add."""
    if not file_id:
        print(f"Skipping add to knowledge collection for '{file_name}' due to missing file ID.")
        return False
    if not KNOWLEDGE_COLLECTION_ID or KNOWLEDGE_COLLECTION_ID == "YOUR_KNOWLEDGE_COLLECTION_ID_HERE":
         print(f"Skipping add to knowledge collection for '{file_name}' because KNOWLEDGE_COLLECTION_ID is not set.")
         return False
        
    print(f"Attempting to add File ID '{file_id}' ('{file_name}') to Knowledge Collection ID '{KNOWLEDGE_COLLECTION_ID}' using endpoint: {collection_add_url}")
    
    # *** Assumption: The payload requires the uploaded file's ID. ***
    # Common key names could be 'file_id', 'doc_id', or similar.
    # Trying 'file_id' as it aligns with the endpoint path '/file/add'.
    # If this fails, check API docs or try 'doc_id'.
    payload = {"file_id": file_id} 
    print(f"  Using payload: {payload}")

    try:
        # Use headers specifying JSON content type
        response = requests.post(collection_add_url, headers=headers_json_payload, json=payload, timeout=30)
        response.raise_for_status() 

        print(f"  Success! Added File ID '{file_id}' to Knowledge Collection ID '{KNOWLEDGE_COLLECTION_ID}'.")
        # Optional: Check response content 
        # try: 
        #    print(f"  Response: {response.json()}")
        # except json.JSONDecodeError:
        #    print(f"  Response Status Code: {response.status_code}, Text: {response.text}") 
        return True

    except requests.exceptions.RequestException as e:
        print(f"  Error adding File ID '{file_id}' to Knowledge Collection ID '{KNOWLEDGE_COLLECTION_ID}': {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"  Response Status Code: {e.response.status_code}")
             try:
                 error_details = e.response.json()
                 print(f"  API Error Details: {error_details}")
             except json.JSONDecodeError:
                 print(f"  Response Text (non-JSON): {e.response.text[:500]}...")
        else:
             print("  No response received from server.")
        return False
    except Exception as e:
        print(f"  An unexpected error occurred adding file ID '{file_id}' to knowledge collection: {e}")
        return False


def main():
    """Main function to find JSON files and process them."""
    print("-" * 30)
    print("Open WebUI Knowledge Base Upload Script (v1 API Endpoints)")
    print("-" * 30)
    print(f"Target Instance: {OPENWEBUI_BASE_URL}")
    print(f"Target Knowledge Collection ID: {KNOWLEDGE_COLLECTION_ID}")
    print(f"Data Folder: {DATA_FOLDER_PATH}")
    print(f"Using Upload URL: {upload_url}")
    print(f"Using Add to Collection URL: {collection_add_url}")
    print("-" * 30)

    # Validate essential configuration
    if "YOUR_API_KEY_HERE" in OPENWEBUI_API_KEY:
         print("\nError: Please replace 'YOUR_API_KEY_HERE' with your actual Open WebUI API Key.")
         return
    if "YOUR_KNOWLEDGE_COLLECTION_ID_HERE" in KNOWLEDGE_COLLECTION_ID:
         print("\nError: Please replace 'YOUR_KNOWLEDGE_COLLECTION_ID_HERE' with the actual Knowledge Collection ID.")
         print("       You can usually find this ID in the Open WebUI interface.")
         return
    if not os.path.isdir(DATA_FOLDER_PATH):
        print(f"Error: Data folder '{DATA_FOLDER_PATH}' not found.")
        print("Please create the folder and place your JSON files inside.")
        return

    # Find all .json files in the data folder
    json_files = glob.glob(os.path.join(DATA_FOLDER_PATH, '*.json'))

    total_files = len(json_files)

    if total_files == 0:
        print(f"No '.json' files found in the '{DATA_FOLDER_PATH}' folder.")
        return

    print(f"Found {total_files} JSON files to process.")

    # --- Processing Loop ---
    success_count = 0
    error_count = 0
    total_script_start_time = time.perf_counter() # Start overall timer

    for i, file_path in enumerate(json_files):
        file_name = os.path.basename(file_path)
        file_start_time = time.perf_counter() # Start timer for this specific file

        print("\n" + "=" * 15 + f" Processing file {i + 1} of {total_files} " + "=" * 15)
        print(f"File: {file_name}")

        # 1. Upload the file and get its ID
        file_id = upload_file(file_path)

        # 2. If upload was successful, add the file ID to the knowledge collection
        added_successfully = False
        if file_id:
            added_successfully = add_file_to_knowledge_collection(file_id, file_name)
            if added_successfully:
                success_count += 1
            else:
                error_count += 1
        else:
            print(f"  Skipping add to knowledge collection for {file_name} because upload failed or File ID was not retrieved.")
            error_count += 1 # Count upload failure as an error for this file

        file_end_time = time.perf_counter()
        file_duration = file_end_time - file_start_time
        print(f"  Total time for {file_name}: {file_duration:.2f} seconds")
        print("=" * (30 + len(f" Processing file {i + 1} of {total_files} ") + 2)) # Match separator length

    total_script_end_time = time.perf_counter() # Stop overall timer
    total_script_duration = total_script_end_time - total_script_start_time

     # --- Final Summary ---
    print("\n" + "-" * 30)
    print("Processing Complete")
    print("-" * 30)
    print(f"Successfully processed (uploaded AND added): {success_count} files.")
    print(f"Failed or Skipped:                         {error_count} files.")
    print(f"Total files attempted:                     {total_files} files.")
    print(f"Total execution time:                      {total_script_duration:.2f} seconds")
    if total_files > 0:
        avg_time = total_script_duration / total_files
        print(f"Average time per file:                   {avg_time:.2f} seconds")
    print("-" * 30)
      

if __name__ == "__main__":
    main()