import os
import json
from langchain.llms import OpenAI

class OutreachSequenceGenerator:
    def __init__(self):
        self.llm = OpenAI(temperature=0.3, max_tokens=2048)
    
    def generate_sequence(self, campaign_info):
        """
        Generate a tailored outreach sequence based on campaign information
        
        campaign_info: Dict containing campaign details like:
        - target_role
        - industry
        - company_values
        - unique_selling_points
        - etc.
        """
        prompt = f"""
        Create a personalized talent outreach sequence for the following campaign:
        
        Target Role: {campaign_info.get('target_role', 'Software Engineer')}
        Industry: {campaign_info.get('industry', 'Technology')}
        Company Values: {campaign_info.get('company_values', 'Innovation, Collaboration, Excellence')}
        Unique Selling Points: {campaign_info.get('unique_selling_points', 'Remote-first, Competitive salary, Growth opportunities')}
        
        The sequence should include:
        1. Initial outreach email
        2. Follow-up message (LinkedIn or email)
        3. Final follow-up
        
        The key for the JSON object should be the step1, step2, etc.

        For each step, include:
        - channel (Email, LinkedIn, etc.)
        - subject_line line (if email)
        - timing (e.g., "Send 3 days after initial email")
        - message_content
        
        IMPORTANT: Keep messages concise. Each message content should be under 150 words.

        Format the response strictly as a JSON object.
        """
        # - Message content with personalization variables like {candidate_name}, {company_name}, etc.
        response = self.llm.invoke(prompt)
        
        # print(f"Sequence LLM Response: {response}")
        # Parse and validate the response
        try:
            sequence = json.loads(response)
            return sequence
        except json.JSONDecodeError:
            # If the LLM doesn't return valid JSON, try to fix it
            # This is a simplified approach
            return {
                "error": "Could not generate valid sequence",
                "raw_response": response
            }
    
    def edit_sequence(self, sequence, edit_instructions):
        """
        Edit an existing sequence based on user feedback
        
        sequence: Existing sequence JSON
        edit_instructions: Natural language instructions for edits
        """
        prompt = f"""
        Edit the following outreach sequence according to these instructions:
        
        Original Sequence:
        {json.dumps(sequence, indent=2)}
        
        Edit Instructions:
        {edit_instructions}

        The key for the JSON object should be the step1, step2, etc.

        For each step, include:
        - Channel (Email, LinkedIn, etc.)
        - Subject line (if email)
        - Timing (e.g., "Send 3 days after initial email")
        - Message content
        
        IMPORTANT: Keep messages concise. Each message content should be under 150 words.
        
        Return the edited sequence as a JSON object with the same structure.
        """
        
        response = self.llm(prompt)
        
        try:
            edited_sequence = json.loads(response)
            return edited_sequence
        except json.JSONDecodeError:
            return {
                "error": "Could not generate valid edited sequence",
                "raw_response": response
            }
