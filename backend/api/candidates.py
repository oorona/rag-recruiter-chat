# backend/api/candidates.py
from flask import Blueprint, jsonify, abort
from backend.services import candidate_service
from backend.utils.logger import logger

candidates_bp = Blueprint('candidates', __name__, url_prefix='/api/candidates')

@candidates_bp.route('', methods=['GET'])
def get_candidate_list():
    """API endpoint to get the list of all candidates."""
    logger.info("Received request for candidate list.")
    candidates = candidate_service.list_candidates()
    return jsonify(candidates)

@candidates_bp.route('/<candidate_id>/markdown', methods=['GET'])
def get_candidate_markdown_content(candidate_id):
    """API endpoint to get the markdown content for a specific candidate."""
    logger.info(f"Received request for markdown for candidate_id: {candidate_id}")
    markdown_content = candidate_service.get_candidate_markdown(candidate_id)
    if markdown_content is None:
        logger.warning(f"Markdown not found for candidate_id: {candidate_id}")
        abort(404, description=f"Markdown content for candidate '{candidate_id}' not found.")
    return jsonify({"markdown": markdown_content})