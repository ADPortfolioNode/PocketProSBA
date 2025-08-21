# services/chat_service.py
from ..models.chat import ChatMessage, db

def create_chat_message(user_id, message):
    new_message = ChatMessage(user_id=user_id, message=message)
    db.session.add(new_message)
    db.session.commit()
    return new_message

def get_all_chat_messages():
    return ChatMessage.query.all()

def update_chat_message(message_id, new_message):
    message = ChatMessage.query.get(message_id)
    if message:
        message.message = new_message
        db.session.commit()
        return message
    return None