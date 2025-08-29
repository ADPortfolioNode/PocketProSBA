# routes/chat.py
from flask import Blueprint, request, jsonify
from services.chat_service import create_chat_message, get_all_chat_messages, update_chat_message

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('', methods=['GET'])
def get_messages():
    messages = get_all_chat_messages()
    return jsonify([{'id': msg.id, 'user_id': msg.user_id, 'message': msg.message, 'timestamp': msg.timestamp} for msg in messages])

@chat_bp.route('', methods=['POST'])
def post_message():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    if not user_id or not message:
        return jsonify({'error': 'User ID and message are required'}), 400
    new_message = create_chat_message(user_id, message)
    return jsonify({'id': new_message.id, 'user_id': new_message.user_id, 'message': new_message.message, 'timestamp': new_message.timestamp}), 201

@chat_bp.route('/<int:message_id>', methods=['PUT'])
def put_message(message_id):
    data = request.json
    new_message = data.get('message')
    if not new_message:
        return jsonify({'error': 'New message content is required'}), 400
    updated_message = update_chat_message(message_id, new_message)
    if updated_message:
        return jsonify({'id': updated_message.id, 'user_id': updated_message.user_id, 'message': updated_message.message, 'timestamp': updated_message.timestamp})
    return jsonify({'error': 'Message not found'}), 404