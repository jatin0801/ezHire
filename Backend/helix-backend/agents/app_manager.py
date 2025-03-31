import json
from agents.hr_agent import HRAgent
from agents.outreach_agent import OutreachSequenceGenerator
from models.database import get_db_connection

class HROutreachManager:
    def __init__(self):
        # Initialize components
        self.hr_agent = HRAgent()
        self.outreach_generator = OutreachSequenceGenerator()
        
    def handle_chat(self, user_id, campaign_id, message, conversation_id=None):
        """Handle a chat message with context"""
        campaign_context = self._get_campaign_context(campaign_id) if campaign_id else ""
        
        full_message = "User's Request: " + message
        if campaign_context:
            full_message = full_message + "\n" + "Campaign context: " + campaign_context

        # full_message = campaign_context + message if campaign_context else message
        response = self.hr_agent.chat(full_message, conversation_id)
        
        # Store conversation
        new_conversation_id = self._store_conversation(user_id, campaign_id, message, response, conversation_id)
        # print("=====Response=====")
        # print(response)
        # formatted_output = response['output'].replace("'", '"')
        # resp = json.loads(formatted_output)
        # print("=====Resp=====")
        # print(resp)
        # output = resp['output']
        # campaign_id = resp.get('campaign_id', campaign_id)
        # message = resp['message']
        return {
            "response": response,
            # "output": json.loads(output),
            # "campaign_id": campaign_id,
            # "message": message,
            "conversation_id": new_conversation_id
        }
    
    def generate_campaign_sequence(self, campaign_id, additional_info=None):
        """Generate a sequence for a campaign"""
        # Get campaign info
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}
            
        # Combine with additional info
        campaign_info = {
            "target_role": campaign['target_role'],
            "industry": campaign['industry']
        }
        
        if additional_info:
            campaign_info.update(additional_info)
            
        # Generate sequence
        sequence = self.outreach_generator.generate_sequence(campaign_info)
        
        # Store sequence
        sequence_id = self._store_sequence(campaign_id, sequence)
        
        return {
            "sequence_id": sequence_id,
            "sequence": sequence
        }
    
    def edit_sequence(self, sequence_id, edit_instructions):
        """Edit an existing sequence"""
        # Get existing sequence
        sequence = self._get_sequence(sequence_id)
        if not sequence:
            return {"error": "Sequence not found"}
            
        # Edit sequence
        edited_sequence = self.outreach_generator.edit_sequence(sequence['sequence_data'], edit_instructions)
        
        # Store new version
        new_sequence_id = self._store_sequence(
            sequence['campaign_id'], 
            edited_sequence['sequence_data'], 
            version=(sequence['version'] + 1)
        )
        
        return {
            "sequence_id": new_sequence_id,
            "sequence": edited_sequence
        }
    
    def create_campaign(self, user_id, name, description=None, target_role=None, industry=None):
        """Create a new campaign"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO campaigns (user_id, name, description, target_role, industry) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (user_id, name, description, target_role, industry)
        )
        
        campaign_id = cur.fetchone()['id']
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"campaign_id": campaign_id, "message": "Campaign created successfully"}
    
    # Helper methods for database operations
    def _get_campaign(self, campaign_id):
        """Get campaign info from database"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM campaigns WHERE id = %s", (campaign_id,))
        campaign = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return campaign
        
    def _get_campaign_context(self, campaign_id):
        """Get campaign context string"""
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return ""
            
        context = f"Working on campaign: {campaign['name']} (campaign_id: {campaign_id})"
        
        if campaign['target_role']:
            context += f" for {campaign['target_role']}"
            
        if campaign['industry']:
            context += f" in the {campaign['industry']} industry"
            
        context += ". "
        
        return context
        
    def _store_conversation(self, user_id, campaign_id, message, response, conversation_id=None):
        """Store conversation in database"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        response_to_store = response
        if isinstance(response, dict):
            response_to_store = response
        else:
            try:
                response_to_store = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                response_to_store = {
                    "message": str(response),
                    "action_tool": "Unknown",
                    "output": "Conversation response"
                }
        
        new_messages = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response_to_store}
        ]
        
        if conversation_id:
            # Get existing conversation
            cur.execute("SELECT messages FROM conversations WHERE id = %s", (conversation_id,))
            conversation = cur.fetchone()
            
            if conversation:
                # Update existing conversation
                messages = conversation['messages']
                messages.extend(new_messages)
                
                cur.execute(
                    "UPDATE conversations SET messages = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id",
                    (json.dumps(messages), conversation_id)
                )
                result = cur.fetchone()
                new_conversation_id = result['id']
            else:
                # Create new conversation if ID not found
                cur.execute(
                    "INSERT INTO conversations (user_id, campaign_id, messages) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, campaign_id, json.dumps(new_messages))
                )
                result = cur.fetchone()
                new_conversation_id = result['id']
        else:
            # Create new conversation
            cur.execute(
                "INSERT INTO conversations (user_id, campaign_id, messages) VALUES (%s, %s, %s) RETURNING id",
                (user_id, campaign_id, json.dumps(new_messages))
            )
            result = cur.fetchone()
            new_conversation_id = result['id']
        
        conn.commit()
        cur.close()
        conn.close()
        
        return new_conversation_id
        
    def _get_sequence(self, sequence_id):
        """Get sequence from database"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM outreach_sequences WHERE id = %s", (sequence_id,))
        sequence = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return sequence
        
    def _store_sequence(self, campaign_id, sequence, version=1):
        """Store sequence in database"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO outreach_sequences (campaign_id, sequence_data, version) VALUES (%s, %s, %s) RETURNING id",
            (campaign_id, json.dumps(sequence), version)
        )
        
        sequence_id = cur.fetchone()['id']
        
        conn.commit()
        cur.close()
        conn.close()
        
        return sequence_id