# backend/api/chat.py
from flask import Blueprint, request, jsonify, abort
from backend.services import chat_service, candidate_service
from backend.utils.logger import logger

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('', methods=['POST'])
def handle_chat():
    """
    API endpoint to handle chat messages.
    It *always* prepends a hidden 'user' message containing the candidate context
    to the message list sent to the LLM. Returns reply and usage stats.
    """
    data = request.get_json()
    if not data or 'message' not in data or 'history' not in data or 'candidate_id' not in data:
        logger.warning("Chat request missing required fields: 'message', 'history', 'candidate_id'.")
        abort(400, description="Missing 'message', 'history', or 'candidate_id' in request body.")

    actual_user_message_content = data['message']
    # History received from client (contains only VISIBLE user <-> assistant turns)
    visible_conversation_history = data['history']
    candidate_id = data['candidate_id']

    logger.info(f"Handling chat message for candidate: {candidate_id}")
    logger.debug(f"Visible history received from client: {visible_conversation_history}")

    # --- Always Prepare Context and Assemble Full Message List ---

    # 1. Fetch candidate details for context
    markdown_content = candidate_service.get_candidate_markdown(candidate_id)
    candidate_display_name = candidate_id # Fallback
    try:
        all_candidates = candidate_service.list_candidates()
        found_candidate = next((c for c in all_candidates if c['id'] == candidate_id), None)
        if found_candidate:
            candidate_display_name = found_candidate['display_name']
    except Exception as e:
        logger.warning(f"Could not retrieve display name for {candidate_id}: {e}")

    # 2. Generate the content for the hidden first 'user' message
    if markdown_content:
        hidden_user_message_content = chat_service.format_context_as_user_message_content(
            candidate_display_name, markdown_content
        )
    else:
        logger.warning(f"Markdown not found for {candidate_id}. Using fallback context message.")
        hidden_user_message_content = (
            f"Note: Detailed information for candidate '{candidate_display_name}' could not be loaded. "
            "Please answer the following questions based on general knowledge, "
            "acknowledging the lack of specific details."
        )

    # 3. Construct the hidden first user message object
    hidden_context_user_message = {"role": "user", "content": hidden_user_message_content}

    # 4. Construct the full list of messages to send to the LLM API
    messages_to_send = [hidden_context_user_message] + visible_conversation_history + [{"role": "user", "content": actual_user_message_content}]

    logger.debug(f"Prepared full message list for LLM (count: {len(messages_to_send)}) for {candidate_id}. First message role: {messages_to_send[0]['role']}")

    # --- Call LLM Service ---
    # The service now returns {'reply': ..., 'usage': ..., 'error': ...}
    service_result = chat_service.call_llm_api(messages_to_send)

    # --- Handle Response ---
    if service_result['error']:
        # If the service returned an error message
        error_msg = service_result['error']
        logger.warning(f"LLM service call failed for {candidate_id}, returning error to client: {error_msg}")
        # Use 500 for simplicity, could use others (502, 503) depending on error
        abort(500, description=error_msg)

    elif service_result['reply'] is not None:
        # Success: We have a reply, and potentially usage stats
        reply_content = service_result['reply']
        usage_stats = service_result['usage'] # This might be None if API didn't provide it

        logger.info(f"Sending successful reply and usage stats for {candidate_id} back to client.")
        return jsonify({
            "reply": reply_content,
            "usage": usage_stats  # Send usage stats (or null) to frontend
        })
    else:
        # This case handles if 'error' is None but 'reply' is also None (e.g., content parsing failed but usage was present)
        # Or if the LLM genuinely returned an empty string reply. We should still return the usage info.
        # Let's return an empty reply but include usage.
        logger.warning(f"LLM service returned no error but reply content was None/empty for {candidate_id}. Returning empty reply.")
        return jsonify({
            "reply": "", # Return empty string if reply was None but no error occurred
            "usage": service_result['usage']
        })