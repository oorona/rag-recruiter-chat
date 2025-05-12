# backend/services/chat_service.py
import requests
import os
import re
from backend.utils.logger import logger

# --- Directory Setup ---
MDATA_DIR_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mdata'))
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

# --- Candidate Data Functions ---
# (list_candidates and get_candidate_markdown remain unchanged from previous version)
def list_candidates():
    candidates = []
    try:
        if not os.path.isdir(MDATA_DIR):
             logger.error(f"Cannot list candidates. Directory not found: {MDATA_DIR}")
             return []
        for filename in os.listdir(MDATA_DIR):
            if filename.lower().endswith(".md"):
                candidate_id = filename[:-3]
                name_without_trailing_numbers = re.sub(r'_?\d+$', '', candidate_id)
                display_name = name_without_trailing_numbers.replace("_", " ")
                candidates.append({
                    "id": candidate_id,
                    "display_name": display_name
                })
        candidates.sort(key=lambda x: x['display_name'])
        logger.info(f"Found {len(candidates)} candidates. Display names cleaned.")
    except FileNotFoundError:
        logger.error(f"Candidate data directory not found: {MDATA_DIR}")
    except Exception as e:
        logger.error(f"Error listing candidates: {e}", exc_info=True)
    return candidates

def get_candidate_markdown(candidate_id: str):
    if ".." in candidate_id or "/" in candidate_id or "\\" in candidate_id:
         logger.warning(f"Invalid candidate_id requested: {candidate_id}")
         return None
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

# --- LLM Interaction ---
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_TOKEN = os.getenv('LLM_API_TOKEN')
LLM_MODEL = os.getenv('LLM_MODEL')

# --- Load Context Prompt Template ---
DEFAULT_CONTEXT_PROMPT_TEMPLATE = (
    "Here is the available information about the candidate '{candidate_name}'. "
    "Please use only this information to answer my following questions about them. "
    "If the answer is not present in this information, state that.\n\n"
    "--- Candidate Information Start ---\n"
    "{markdown_content}\n"
    "--- Candidate Information End ---\n\n"
    "Now, I will ask my questions."
)
CONTEXT_PROMPT_TEMPLATE = os.getenv('CONTEXT_PROMPT_TEMPLATE', DEFAULT_CONTEXT_PROMPT_TEMPLATE)

# Log whether the default or env template is used
if CONTEXT_PROMPT_TEMPLATE == DEFAULT_CONTEXT_PROMPT_TEMPLATE and not os.getenv('CONTEXT_PROMPT_TEMPLATE'):
    logger.warning("CONTEXT_PROMPT_TEMPLATE not found in .env, using default value.")
else:
    logger.info("Using CONTEXT_PROMPT_TEMPLATE from .env file.")
# --- End Load Context Prompt Template ---


if not all([LLM_API_URL, LLM_API_TOKEN, LLM_MODEL]):
    logger.error("LLM configuration missing in .env file (LLM_API_URL, LLM_API_TOKEN, LLM_MODEL)")

def format_context_as_user_message_content(candidate_name: str, markdown_content: str) -> str:
    """
    Formats the candidate markdown into a string suitable for the content
    of the hidden first 'user' message, using the template from .env.
    """
    formatted_name = candidate_name.replace("_", " ")
    try:
        # Use the loaded template string (from .env or default) and substitute values
        content = CONTEXT_PROMPT_TEMPLATE.format(
            formatted_name=formatted_name        )
        logger.debug(f"Formatted hidden user message content using template for: {formatted_name}")
        logger.debug(f"Formatted content: {content}")
        return content
    except KeyError as e:
         # Handle case where the template in .env is missing a required placeholder
         logger.error(f"Error formatting context prompt template. Missing key: {e}. Check CONTEXT_PROMPT_TEMPLATE in .env. Using basic fallback.", exc_info=True)
         # Provide a very basic fallback to avoid crashing
         return f"Context for {formatted_name}:\n{markdown_content}\nPlease answer questions about this context."
    except Exception as e:
        logger.error(f"Unexpected error formatting context prompt: {e}. Using basic fallback.", exc_info=True)
        return f"Context for {formatted_name}:\n{markdown_content}\nPlease answer questions about this context."


def call_llm_api(messages: list):
    """
    Calls the external LLM API. (Implementation remains the same as previous step)

    Returns:
        dict: {'reply': str|None, 'usage': dict|None, 'error': str|None}
    """
    # (No changes needed in the call_llm_api implementation itself)
    if not all([LLM_API_URL, LLM_API_TOKEN, LLM_MODEL]):
         error_msg = "LLM service is not configured correctly."
         logger.error(error_msg)
         return {'reply': None, 'usage': None, 'error': error_msg}

    headers = {
        'Authorization': f'Bearer {LLM_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
      "model": LLM_MODEL,
      "messages": messages,
    }

    log_messages_preview = [
        {'role': msg['role'], 'content': msg['content'][:100] + '...' if len(msg.get('content','')) > 100 else msg.get('content','')}
        for msg in messages
    ]
    logger.debug(f"Sending request to LLM: {LLM_API_URL} model {LLM_MODEL}. Messages preview: {log_messages_preview}")

    try:
        response = requests.post(LLM_API_URL, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_json = response.json()
        logger.debug(f"LLM Raw Response: {response_json}")

        reply_content = None
        usage_stats = None
        error_msg = None

        choices = response_json.get("choices")
        if choices and isinstance(choices, list) and len(choices) > 0:
            message = choices[0].get("message")
            if message and isinstance(message, dict):
                 content = message.get("content")
                 if content is not None:
                     reply_content = content.strip()

        usage_stats = response_json.get("usage")
        if not isinstance(usage_stats, dict):
             logger.warning("Usage stats not found or not a dictionary in LLM response.")
             usage_stats = None

        if reply_content is not None:
            logger.info("Successfully received response and usage stats from LLM.")
            return {'reply': reply_content, 'usage': usage_stats, 'error': None}
        else:
             error_msg = "LLM response format unexpected (missing content)."
             logger.error(f"{error_msg} Response: {response_json}")
             return {'reply': None, 'usage': usage_stats, 'error': error_msg}

    except requests.exceptions.Timeout:
        error_msg = "The request to the language model timed out."
        logger.error(error_msg, exc_info=True)
        return {'reply': None, 'usage': None, 'error': error_msg}
    except requests.exceptions.RequestException as e:
        error_message = "Failed to communicate with the language model."
        status_code = None
        if e.response is not None:
             status_code = e.response.status_code
             if status_code == 401: error_message = "Authentication error with the language model API."
             elif status_code == 404: error_message = "Language model API endpoint not found."
             elif status_code == 429: error_message = "Rate limit exceeded with the language model API."
             elif status_code >= 500: error_message = "The language model server encountered an error."
             else: error_message = f"Language model API returned status {status_code}."
             logger.error(f"LLM API Error: {error_message}. Status: {status_code}. Body: {e.response.text}", exc_info=False)
        else:
             logger.error(f"LLM API Error: {error_message}. Error details: {e}", exc_info=True)
        return {'reply': None, 'usage': None, 'error': error_message}
    except Exception as e:
        error_msg = "An unexpected error occurred during LLM call."
        logger.error(error_msg, exc_info=True)
        return {'reply': None, 'usage': None, 'error': error_msg}