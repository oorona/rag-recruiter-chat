# backend/services/candidate_service.py
import os
import re  # Import the regular expression module
from backend.utils.logger import logger

# Determine the absolute path to the mdata folder relative to this script
# Assuming mdata is one level up from the backend directory if MDATA_FOLDER env var isn't set
MDATA_DIR_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mdata'))
# Use environment variable if set, otherwise use default. Resolve relative paths from project root.
_mdata_folder_env = os.getenv('MDATA_FOLDER')
if _mdata_folder_env:
    if not os.path.isabs(_mdata_folder_env):
        MDATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', _mdata_folder_env))
    else:
        MDATA_DIR = _mdata_folder_env
else:
    MDATA_DIR = MDATA_DIR_DEFAULT


logger.info(f"Using mdata directory: {MDATA_DIR}")
if not os.path.isdir(MDATA_DIR):
    logger.error(f"mdata directory not found at: {MDATA_DIR}. Please create it or check MDATA_FOLDER in .env")
    # Consider raising an exception here if the directory is critical at startup


def list_candidates():
    """
    Lists candidates based on markdown files in the mdata directory.
    Removes trailing numbers (preceded by an optional underscore) from the
    filename *only* for the display name.
    Returns a list of dictionaries with:
      - 'id': Original filename without .md extension (e.g., 'JOHN_SMITH_2005').
      - 'display_name': Cleaned name with trailing numbers removed and
                        underscores replaced by spaces (e.g., 'JOHN SMITH').
    """
    candidates = []
    try:
        if not os.path.isdir(MDATA_DIR):
             logger.error(f"Cannot list candidates. Directory not found: {MDATA_DIR}")
             return []
        for filename in os.listdir(MDATA_DIR):
            if filename.lower().endswith(".md"):
                # 1. Get the full ID (original filename without .md extension)
                candidate_id = filename[:-3]

                # 2. Prepare the name for display:
                #    Use regex to remove an optional underscore `_?` followed by
                #    one or more digits `\d+` occurring at the end `$` of the candidate_id string.
                #    Replace this match with an empty string ''.
                name_without_trailing_numbers = re.sub(r'_?\d+$', '', candidate_id)

                # 3. Create the final display name from the cleaned name:
                #    Replace remaining underscores with spaces.
                display_name = name_without_trailing_numbers.replace("_", " ")

                # 4. Append to the list using the original candidate_id and the cleaned display_name
                candidates.append({
                    "id": candidate_id,           # Use original ID for file access & API calls
                    "display_name": display_name  # Use cleaned name for the UI list
                })

        # Sort candidates alphabetically by their display name
        candidates.sort(key=lambda x: x['display_name'])
        logger.info(f"Found {len(candidates)} candidates. Display names cleaned.")
    except FileNotFoundError:
        logger.error(f"Candidate data directory not found: {MDATA_DIR}")
    except Exception as e:
        logger.error(f"Error listing candidates: {e}", exc_info=True)
    return candidates

def get_candidate_markdown(candidate_id: str):
    """
    Reads and returns the markdown content for a given candidate ID.
    The candidate_id corresponds to the original filename without the .md extension
    (e.g., 'JOHN_SMITH_2005').
    """
    # Basic sanitization to prevent directory traversal
    if ".." in candidate_id or "/" in candidate_id or "\\" in candidate_id:
         logger.warning(f"Invalid candidate_id requested: {candidate_id}")
         return None

    # Construct path using the original candidate_id which includes numbers if they existed
    file_path = os.path.join(MDATA_DIR, f"{candidate_id}.md")
    logger.debug(f"Attempting to read markdown from: {file_path}")
    try:
        if not os.path.exists(file_path):
             logger.warning(f"Markdown file not found for candidate: {candidate_id} at path {file_path}")
             return None
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"Successfully read markdown for candidate: {candidate_id}")
            return content
    except Exception as e:
        logger.error(f"Error reading markdown for candidate {candidate_id}: {e}", exc_info=True)
        return None