from flask import Blueprint, request, jsonify
from agents.app_manager import HROutreachManager
from models.database import get_db_connection

chat_bp = Blueprint('chat', __name__)
outreach_manager = HROutreachManager()

@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    campaign_id = data.get('campaign_id')
    message = data.get('message')
    conversation_id = data.get('conversation_id')
    
    if not all([user_id, message]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Use the centralized manager to handle the chat
    result = outreach_manager.handle_chat(
        user_id=user_id,
        campaign_id=campaign_id,
        message=message,
        conversation_id=conversation_id
    )
    
    return jsonify({
        "response": result["response"],
        "conversation_id": result["conversation_id"]
    })

@chat_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get conversation history"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM conversations WHERE id = %s", (conversation_id,))
    conversation = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
        
    return jsonify({
        "conversation_id": conversation['id'],
        "user_id": conversation['user_id'],
        "campaign_id": conversation['campaign_id'],
        "messages": conversation['messages'],
        "created_at": conversation['created_at'],
        "updated_at": conversation['updated_at']
    })