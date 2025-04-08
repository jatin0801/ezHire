from flask import Blueprint, request, jsonify
from agents.app_manager import HROutreachManager
from models.database import get_db_connection

campaign_bp = Blueprint('campaign', __name__)
outreach_manager = HROutreachManager()

@campaign_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    description = data.get('description')
    target_role = data.get('target_role')
    industry = data.get('industry')
    
    if not all([user_id, name]):
        return jsonify({"error": "Missing required fields"}), 400
    
    result = outreach_manager.create_campaign(
        user_id=user_id,
        name=name,
        description=description,
        target_role=target_role,
        industry=industry
    )
    
    return jsonify(result)

@campaign_bp.route('/campaigns/<int:campaign_id>/sequence', methods=['POST'])
def generate_sequence(campaign_id):
    data = request.json
    
    result = outreach_manager.generate_campaign_sequence(
        campaign_id=campaign_id,
        additional_info={
            "company_values": data.get('company_values'),
            "unique_selling_points": data.get('unique_selling_points')
        }
    )
    
    if "error" in result:
        return jsonify(result), 404
        
    return jsonify(result)

@campaign_bp.route('/sequences/<int:sequence_id>/edit', methods=['POST'])
def edit_sequence(sequence_id):
    data = request.json
    edit_instructions = data.get('edit_instructions')
    
    if not edit_instructions:
        return jsonify({"error": "Missing edit instructions"}), 400
    
    result = outreach_manager.edit_sequence(
        sequence_id=sequence_id,
        edit_instructions=edit_instructions
    )
    
    if "error" in result:
        return jsonify(result), 404
        
    return jsonify(result)

@campaign_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Get all campaigns for a user"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM campaigns WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    campaigns = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        "campaigns": campaigns
    })

@campaign_bp.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get a specific campaign"""
    campaign = outreach_manager._get_campaign(campaign_id)
    
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
        
    return jsonify(campaign)

@campaign_bp.route('/campaigns/<int:campaign_id>/sequences', methods=['GET'])
def get_campaign_sequences(campaign_id):
    """Get all sequences for a campaign"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM outreach_sequences WHERE campaign_id = %s ORDER BY version", (campaign_id,))
    sequences = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        "sequences": sequences
    })