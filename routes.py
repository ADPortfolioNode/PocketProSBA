from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

