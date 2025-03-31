from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from models.database import setup_database
from models.vector_store import initialize_pinecone
from routes.chat_routes import chat_bp
from routes.campaign_routes import campaign_bp

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Configure database and vector store
setup_database()
# pinecone_index = initialize_pinecone()

# Register blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(campaign_bp)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        "status": "running",
        "database": "connected" if os.getenv('DATABASE_URL') else "disconnected",
        # "pinecone": "connected" if pinecone_index else "disconnected"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5080))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'False') == 'True')
