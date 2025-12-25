"""
Telegram Health Insurance Bot - AWS App Runner Compatible
Adds a simple health check endpoint for AWS
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai
from threading import Thread
from flask import Flask

from knowledge_base import HealthInsuranceKnowledgeBase
from language_detector import LanguageDetector
from response_formatter import ResponseFormatter
from company_loader import CompanyKnowledge

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini - Support both API Key and Vertex AI
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
use_vertex_ai = os.getenv('USE_VERTEX_AI', 'false').lower() == 'true'

if api_key and not use_vertex_ai:
    logger.info("🔑 Using Gemini API Key")
    genai.configure(api_key=api_key)
    # Using gemini-2.0-flash-001 for production
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-001')
elif use_vertex_ai or (not api_key and os.getenv('GOOGLE_CLOUD_PROJECT')):
    # Use Vertex AI (Service Account)
    try:
        logger.info("☁️ Using Google Cloud Vertex AI (Service Account)")
        from vertexai.preview.generative_models import GenerativeModel
        import vertexai
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'eg-konecta-sandbox')
        location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        
        vertexai.init(project=project_id, location=location)
        gemini_model = GenerativeModel('gemini-2.0-flash-001')
        logger.info(f"✅ Vertex AI initialized: {project_id} / {location}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Vertex AI: {e}")
        gemini_model = None
        logger.warning("Falling back to knowledge base only")
else:
    gemini_model = None
    logger.warning("No Gemini API key or Vertex AI config found - using knowledge base only")

# Initialize components
kb = HealthInsuranceKnowledgeBase()
lang_detector = LanguageDetector()
formatter = ResponseFormatter()
company_kb = CompanyKnowledge()  # Load company-specific knowledge

logger.info(f"📚 Company knowledge loaded from: {company_kb.company_info['file_path']}")

# Store conversation history per user
conversation_history = {}

def get_conversation_history(user_id: str) -> list:
    """Get or create conversation history for a user"""
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    return conversation_history[user_id]

def add_to_history(user_id: str, role: str, content: str):
    """Add message to conversation history"""
    history = get_conversation_history(user_id)
    history.append({"role": role, "content": content})
    
    # Keep only last 10 messages (5 exchanges)
    if len(history) > 10:
        conversation_history[user_id] = history[-10:]

def clear_history(user_id: str):
    """Clear conversation history for a user"""
    if user_id in conversation_history:
        conversation_history[user_id] = []

# Get Telegram token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in .env file!")
    logger.error("Please add: TELEGRAM_BOT_TOKEN=your_token_here")
    exit(1)

# Flask app for health check (AWS App Runner requirement)
from flask import Flask, request, jsonify

# ... imports ...

# Flask app
flask_app = Flask(__name__)

# Basic CORS support without extra dependencies
@flask_app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@flask_app.route('/')
@flask_app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'omnical-center-bot'}, 200

@flask_app.route('/chat', methods=['POST'])
def web_chat():
    """API Endpoint for Web Chat"""
    try:
        data = request.json
        user_id = data.get('user_id', 'web_user')
        message = data.get('message', '')
        language = data.get('language', 'en') # 'en' or 'ar'
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
            
        logger.info(f"🌐 Web Chat from {user_id}: {message}")
        
        # Use Synchronous processing for Flask to avoid Event Loop issues
        response_text = process_with_ai_sync(message, language, user_id)

        return jsonify({
            'response': response_text,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Web Chat Error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def run_flask():
    """Run Flask in a separate thread"""
    port = int(os.getenv('PORT', 8080))
    # Threaded=True is default, needed for concurrent requests
    flask_app.run(host='0.0.0.0', port=port, debug=False)

# ... rest of telegram handlers ...

async def process_with_ai(query: str, language: str, user_id: str) -> str:
    """Process query using Gemini AI - Shared by Telegram and Web"""
    # ... existing logic ...
    try:
        if not gemini_model:
            # Fallback for no API key 
            return kb.search_faq(query, language) or "Sorry, AI is offline."
            
        # ... logic as before ...
        
        # Get conversation history
        history = get_conversation_history(user_id)
        
        # Build context from history
        context_messages = ""
        if history:
            context_messages = "\n\nPrevious conversation:\n"
            for msg in history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_messages += f"{role}: {msg['content']}\n"
        
        company_context = company_kb.get_summary()

        # Simplified prompt construction for shared use
        prompt_intro = "أنت موظف خدمة عملاء" if language == "ar" else "You are a customer service rep"
        
        prompt = f"""{prompt_intro}
        
Company Context: {company_context}

History:
{context_messages}

User Query: {query}

Provide a helpful, friendly response.
"""
        # Call Gemini
        response = await gemini_model.generate_content_async(prompt)
        answer = response.text
        
        # Add to history
        add_to_history(user_id, "user", query)
        add_to_history(user_id, "assistant", answer)
        
        return formatter.clean_ai_formatting(answer)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "Sorry, I encountered an error."

def process_with_ai_sync(query: str, language: str, user_id: str) -> str:
    """Synchronous version of process_with_ai for Flask"""
    try:
        if not gemini_model:
            return kb.search_faq(query, language) or "Sorry, AI is offline."
            
        history = get_conversation_history(user_id)
        
        context_messages = ""
        if history:
            context_messages = "\n\nPrevious conversation:\n"
            for msg in history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_messages += f"{role}: {msg['content']}\n"
        
        company_context = company_kb.get_summary()

        prompt_intro = "أنت موظف خدمة عملاء" if language == "ar" else "You are a customer service rep"
        
        prompt = f"""{prompt_intro}
        
Company Context: {company_context}

History:
{context_messages}

User Query: {query}

Provide a helpful, friendly response.
"""
        # Call Gemini Synchronously
        response = gemini_model.generate_content(prompt)
        answer = response.text
        
        add_to_history(user_id, "user", query)
        add_to_history(user_id, "assistant", answer)
        
        return formatter.clean_ai_formatting(answer)

    except Exception as e:
        logger.error(f"AI Sync Error: {e}")
        return "Sorry, I encountered an error."

def main():
    """Run the application"""
    # Start Flask API (Blocking call for now, since we only need the Web Chat for this test)
    logger.info("🚀 Starting Web Chat API on port 8080...")
    run_flask()

if __name__ == '__main__':
    main()
