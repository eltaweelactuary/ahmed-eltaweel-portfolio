"""
Smart Document Management System with AI Chatbot
نظام إدارة مستندات ذكي مع شات بوت AI
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
import sqlite3
from datetime import datetime
import hashlib
from pathlib import Path
import mimetypes
import math
import PyPDF2
import docx
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['LOGO_FOLDER'] = 'static/brand'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)

from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from langchain_google_vertexai import ChatVertexAI
except ImportError:
    ChatVertexAI = None

# Configure AI - Support Service Account (Vertex AI) or API Key
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
project_id = os.getenv('GOOGLE_CLOUD_PROJECT')

ai_configured = False

if credentials_path and os.path.exists(credentials_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    ai_configured = True
    print(f"[OK] AI Configured: Using Service Account (Vertex AI) from {os.path.basename(credentials_path)}")
elif api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    ai_configured = True
    print(f"[OK] AI Configured: Using API Key ending in ...{api_key[-4:]}")
else:
    print("[WARNING] No AI configured - set GOOGLE_APPLICATION_CREDENTIALS or GEMINI_API_KEY in .env")

def run_agent_task(prompt):
    """Executes a task using a CrewAI agent"""
    if not ai_configured:
        return "AI Error: AI not configured (missing Credentials or API Key)"

    try:
        # Initialize LLM based on available authentication
        if credentials_path and os.path.exists(credentials_path) and ChatVertexAI:
            llm = ChatVertexAI(
                model_name="gemini-2.0-flash-exp",
                project=project_id,
                temperature=0.7,
                verbose=True
            )
        else:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                verbose=True,
                temperature=0.7,
                google_api_key=api_key
            )

        # Create Agent
        dms_agent = Agent(
            role='Smart Document Assistant',
            goal='Provide accurate, professional, and helpful responses based on document context.',
            backstory="""You are an expert AI assistant for a Document Management System (DMS). 
            You are bilingual (Arabic & English). Your job is to analyze text, answer questions, 
            summarize documents, and enhance notes professionally. You always maintain a helpful 
            and polite tone.""",
            llm=llm,
            verbose=False,
            allow_delegation=False
        )

        # Create Task
        task = Task(
            description=prompt,
            expected_output="A comprehensive and professional response in the requested format/language.",
            agent=dms_agent
        )

        # Create Crew
        crew = Crew(
            agents=[dms_agent],
            tasks=[task],
            verbose=False
        )

        # Execute
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        print(f"CrewAI Error: {e}")
        return f"System Error: {str(e)}"

# Database initialization
def init_db():
    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT NOT NULL,
                  original_filename TEXT NOT NULL,
                  file_path TEXT NOT NULL,
                  file_size INTEGER,
                  file_type TEXT,
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  description TEXT,
                  tags TEXT,
                  content_text TEXT,
                  file_hash TEXT UNIQUE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_message TEXT NOT NULL,
                  bot_response TEXT NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  related_files TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  related_files TEXT,
                  tags TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS favorites
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT NOT NULL,
                  category TEXT DEFAULT 'general',
                  usage_count INTEGER DEFAULT 0,
                  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_text_from_file(file_path, extension):
    text = ""
    try:
        if extension == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        elif extension == 'pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        elif extension == 'docx':
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        # Simple extraction for other types could be added here
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text

def search_in_database(query, search_type='keyword'):
    """Enhanced search with occurrence count and relevance scoring"""
    conn = sqlite3.connect('smart_dms.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    search_query = f"%{query}%"
    c.execute('''SELECT id, filename, original_filename, file_type, upload_date, content_text 
                 FROM files 
                 WHERE original_filename LIKE ? 
                 OR content_text LIKE ? 
                 ORDER BY upload_date DESC''', (search_query, search_query))
    
    results = []
    query_lower = query.lower()
    
    for row in c.fetchall():
        filename = row['original_filename'] or ''
        content = row['content_text'] or ''
        
        # Count occurrences
        filename_count = filename.lower().count(query_lower)
        content_count = content.lower().count(query_lower)
        total_occurrences = filename_count + content_count
        
        # Calculate relevance score (0-100)
        score = 0
        
        # Title match: 40 points max
        if query_lower in filename.lower():
            if filename.lower().startswith(query_lower):
                score += 40  # Exact start match
            else:
                score += 25  # Contains in title
        
        # Content match: 40 points max (logarithmic scale)
        if content_count > 0:
            import math
            content_score = min(40, int(10 * math.log2(content_count + 1)))
            score += content_score
        
        # Recency: 20 points max (newer = higher)
        from datetime import datetime
        try:
            upload_date = datetime.fromisoformat(row['upload_date'].replace('Z', '+00:00'))
            days_old = (datetime.now() - upload_date.replace(tzinfo=None)).days
            recency_score = max(0, 20 - days_old)  # Lose 1 point per day
            score += recency_score
        except:
            score += 10  # Default if date parsing fails
        
        # Find matching snippet
        snippet = ""
        if content and query_lower in content.lower():
            idx = content.lower().find(query_lower)
            start = max(0, idx - 50)
            end = min(len(content), idx + len(query) + 100)
            snippet = "..." + content[start:end] + "..."
        
        results.append({
            'id': row['id'],
            'filename': filename,
            'file_type': row['file_type'],
            'upload_date': row['upload_date'],
            'content_preview': (content)[:500],
            'occurrences': total_occurrences,
            'score': min(100, score),
            'snippet': snippet
        })
    
    conn.close()
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def get_file_content_by_name(filename):
    """Get full file content by filename"""
    conn = sqlite3.connect('smart_dms.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT content_text FROM files WHERE original_filename LIKE ?', (f'%{filename}%',))
    result = c.fetchone()
    conn.close()
    return result['content_text'] if result and result['content_text'] else None

def get_recent_chat_history(limit=5):
    """Get recent chat messages for context"""
    conn = sqlite3.connect('smart_dms.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT user_message, bot_response FROM chat_history ORDER BY id DESC LIMIT ?', (limit,))
    history = []
    for row in reversed(c.fetchall()):
        history.append({'user': row['user_message'], 'bot': row['bot_response']})
    conn.close()
    return history

def ai_chat_response(user_message, context_files=None):
    if not ai_configured:
        return "AI غير متصل. يرجى التحقق من ملف .env"
    
    try:
        # Build context with chat history
        chat_history = get_recent_chat_history(5)
        
        context = """You are a Smart Document Assistant. You help users with their files and documents.
Rules:
- Answer in the SAME language as the user's message (Arabic or English)
- If user mentions a file, use the file content provided below
- Be helpful, professional, and concise
- Remember context from previous messages

"""
        
        # Add chat history for memory
        if chat_history:
            context += "=== Recent Conversation ===\n"
            for msg in chat_history[-3:]:  # Last 3 exchanges
                context += f"User: {msg['user']}\nAssistant: {msg['bot'][:200]}...\n"
            context += "\n"
        
        # Add file content if files are relevant
        if context_files:
            context += "=== Relevant Documents ===\n"
            for file in context_files[:2]:  # Limit to 2 files
                content = file.get('content_preview', '')
                if content:
                    context += f"\n--- {file['filename']} ---\n{content}\n"
            context += "\n"
        
        # Check if user is asking about a specific file
        words = user_message.lower().split()
        for word in words:
            if '.' in word or len(word) > 5:  # Might be filename
                file_content = get_file_content_by_name(word)
                if file_content:
                    context += f"\n=== Content of {word} ===\n{file_content[:3000]}\n"
                    break
        
        context += f"\n=== Current User Message ===\n{user_message}"
        
        return run_agent_task(context)
    except Exception as e:
        return f"AI Error: {str(e)}"

# Routes
@app.route('/')
def index():
    # v1.1 - Forcing template refresh
    return render_template('smart_dms_index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file'}), 400
    
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(file_path)
        
        # Calculate file size and hash after saving
        file_size = os.path.getsize(file_path)
        file_hash = get_file_hash(file_path)
        
        print(f"[DEBUG] Extracting text from {original_filename} ({file_size} bytes)")
        content_text = extract_text_from_file(file_path, file_ext)
        print(f"[DEBUG] Text extraction complete. Sample: {content_text[:50] if content_text else 'NONE'}")
        
        description = request.form.get('description', '')
        tags = request.form.get('tags', '')
        
        try:
            conn = sqlite3.connect('smart_dms.db')
            c = conn.cursor()
            c.execute('''INSERT INTO files 
                         (filename, original_filename, file_path, file_size, file_type, description, tags, content_text, file_hash)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (filename, original_filename, file_path, file_size, file_ext, description, tags, content_text, file_hash))
            conn.commit()
            file_id = c.lastrowid
            conn.close()
            
            return jsonify({'success': True, 'file_id': file_id, 'filename': original_filename})
        except sqlite3.IntegrityError:
            os.remove(file_path)
            return jsonify({'error': 'File exists'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/files', methods=['GET'])
def get_files():
    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    c.execute('''SELECT id, original_filename, file_type, file_size, upload_date, last_modified, description, tags 
                 FROM files ORDER BY upload_date DESC''')
    
    files = []
    for row in c.fetchall():
        files.append({
            'id': row[0],
            'filename': row[1],
            'type': row[2],
            'size': row[3],
            'upload_date': row[4],
            'last_modified': row[5],
            'description': row[6],
            'tags': row[7]
        })
    
    conn.close()
    return jsonify(files)

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    c.execute('SELECT file_path FROM files WHERE id = ?', (file_id,))
    result = c.fetchone()
    
    if result:
        file_path = result[0]
        c.execute('DELETE FROM files WHERE id = ?', (file_id,))
        conn.commit()
        if os.path.exists(file_path):
            os.remove(file_path)
        conn.close()
        return jsonify({'success': True})
    
    conn.close()
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    search_type = data.get('type', 'keyword')
    results = search_in_database(query, search_type)
    return jsonify(results)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message'}), 400
    
    relevant_files = search_in_database(user_message, 'keyword')
    bot_response = ai_chat_response(user_message, relevant_files)
    
    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    related_files_json = json.dumps([f['id'] for f in relevant_files[:5]])
    c.execute('INSERT INTO chat_history (user_message, bot_response, related_files) VALUES (?, ?, ?)',
              (user_message, bot_response, related_files_json))
    conn.commit()
    conn.close()
    
    return jsonify({'response': bot_response, 'relevant_files': relevant_files[:5]})

@app.route('/api/logo', methods=['POST'])
def upload_logo():
    """Upload corporate logo"""
    if 'logo' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['logo']
    if file.filename == '':
        return jsonify({'error': 'No file'}), 400
    
    filename = secure_filename('company_logo.png')
    file_path = os.path.join(app.config['LOGO_FOLDER'], filename)
    file.save(file_path)
    return jsonify({'success': True, 'path': '/static/brand/company_logo.png'})

@app.route('/static/brand/<path:filename>')
def serve_logo(filename):
    return send_from_directory(app.config['LOGO_FOLDER'], filename)

# ============ DUAL CHAT SYSTEM ============

@app.route('/api/chat/notes', methods=['POST'])
def chat_notes():
    """Notes/Summary Chat - Generates ready-to-deliver bilingual notes"""
    if not ai_configured:
        return jsonify({'error': 'AI not configured'}), 503
    
    data = request.json
    user_message = data.get('message', '')
    file_id = data.get('file_id')
    
    if not user_message:
        return jsonify({'error': 'No message'}), 400
    
    # Get file content if specified
    file_content = ""
    filename = ""
    if file_id:
        conn = sqlite3.connect('smart_dms.db')
        c = conn.cursor()
        c.execute('SELECT original_filename, content_text FROM files WHERE id = ?', (file_id,))
        result = c.fetchone()
        conn.close()
        if result:
            filename = result[0]
            file_content = result[1] or ""
    
    # Detect language
    is_arabic = any('\u0600' <= char <= '\u06FF' for char in user_message)
    
    prompt = f"""You are a Professional Note Generator. Create a READY-TO-DELIVER note/memo.

TASK: {user_message}

{"FILE CONTENT (" + filename + "):" if file_content else ""}
{file_content[:4000] if file_content else ""}

OUTPUT REQUIREMENTS:
1. Generate in {'Arabic (العربية)' if is_arabic else 'English'}
2. Use professional, formal language
3. Structure with clear sections
4. Ready for immediate delivery/submission
5. Include key points and summary

FORMAT:
{'=== المذكرة ===' if is_arabic else '=== MEMORANDUM ==='}

{'العنوان:' if is_arabic else 'Subject:'} [subject]
{'التاريخ:' if is_arabic else 'Date:'} [current date]

{'المحتوى:' if is_arabic else 'Content:'}
[well-structured content]

{'الملخص:' if is_arabic else 'Summary:'}
[brief summary]
"""
    
    try:
        response = run_agent_task(prompt)
        return jsonify({
            'response': response,
            'type': 'note',
            'language': 'ar' if is_arabic else 'en'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/file', methods=['POST'])
def chat_file():
    """File Chat - Interactive conversation with document content (Gemini-like)"""
    if not ai_configured:
        return jsonify({'error': 'AI not configured'}), 503
    
    data = request.json
    user_message = data.get('message', '')
    file_id = data.get('file_id')
    
    if not user_message:
        return jsonify({'error': 'No message'}), 400
    
    if not file_id:
        return jsonify({'error': 'No file selected'}), 400
    
    # Get file content
    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    c.execute('SELECT original_filename, content_text FROM files WHERE id = ?', (file_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'File not found'}), 404
    
    filename, content = result
    
    if not content:
        return jsonify({'error': 'File has no text content'}), 400
    
    # Detect language
    is_arabic = any('\u0600' <= char <= '\u06FF' for char in user_message)
    
    prompt = f"""You are an AI Document Assistant analyzing a file.

DOCUMENT: {filename}
CONTENT:
{content[:6000]}

USER QUESTION: {user_message}

INSTRUCTIONS:
- Answer based ONLY on the document content above
- Respond in {'Arabic' if is_arabic else 'English'} (same as user's language)
- Be specific and cite relevant parts
- If information not in document, say so clearly
"""
    
    try:
        response = run_agent_task(prompt)
        return jsonify({
            'response': response,
            'type': 'file_chat',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ FAVORITES SYSTEM ============

@app.route('/api/favorites', methods=['GET', 'POST'])
def favorites():
    """Manage favorite questions"""
    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute('SELECT id, question, category, usage_count FROM favorites ORDER BY usage_count DESC')
        favorites_list = []
        for row in c.fetchall():
            favorites_list.append({
                'id': row[0],
                'question': row[1],
                'category': row[2],
                'usage_count': row[3]
            })
        conn.close()
        return jsonify(favorites_list)
    
    elif request.method == 'POST':
        data = request.json
        question = data.get('question', '')
        category = data.get('category', 'general')
        
        if not question:
            conn.close()
            return jsonify({'error': 'No question'}), 400
        
        # Check if exists
        c.execute('SELECT id FROM favorites WHERE question = ?', (question,))
        existing = c.fetchone()
        
        if existing:
            c.execute('UPDATE favorites SET usage_count = usage_count + 1 WHERE id = ?', (existing[0],))
        else:
            c.execute('INSERT INTO favorites (question, category) VALUES (?, ?)', (question, category))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/favorites/<int:fav_id>', methods=['DELETE'])
def delete_favorite(fav_id):
    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    c.execute('DELETE FROM favorites WHERE id = ?', (fav_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'GET':
        conn = sqlite3.connect('smart_dms.db')
        c = conn.cursor()
        c.execute('SELECT id, title, content, created_date, last_modified, tags FROM notes ORDER BY last_modified DESC')
        
        notes_list = []
        for row in c.fetchall():
            notes_list.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'created_date': row[3],
                'last_modified': row[4],
                'tags': row[5]
            })
        
        conn.close()
        return jsonify(notes_list)
    
    elif request.method == 'POST':
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')
        tags = data.get('tags', '')
        
        conn = sqlite3.connect('smart_dms.db')
        c = conn.cursor()
        c.execute('INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)', (title, content, tags))
        conn.commit()
        note_id = c.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'note_id': note_id})

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    c.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/notes/<int:note_id>/enhance', methods=['POST'])
def enhance_note(note_id):
    """AI-powered professional note enhancement in both languages"""
    if not ai_configured:
        return jsonify({'error': 'AI not configured'}), 503

    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    c.execute('SELECT title, content FROM notes WHERE id = ?', (note_id,))
    result = c.fetchone()
    conn.close()

    if not result:
        return jsonify({'error': 'Note not found'}), 404

    title, content = result
    
    try:
        prompt = f"""You are a professional writing assistant. Enhance this note into TWO versions (Arabic & English).

Make it:
- Professional and eloquent
- Well-structured with clear paragraphs
- Grammatically perfect
- Detailed and comprehensive

Original Title: {title}
Original Content: {content}

Provide:
1. Enhanced ARABIC version (احترافي وبليغ)
2. Enhanced ENGLISH version (professional & eloquent)

Format:
[ARABIC]
<enhanced arabic content>

[ENGLISH]
<enhanced english content>
"""
        
        enhanced_text = run_agent_task(prompt)
        
        # Extract sections
        arabic_section = ""
        english_section = ""
        
        if "[ARABIC]" in enhanced_text and "[ENGLISH]" in enhanced_text:
            parts = enhanced_text.split("[ENGLISH]")
            arabic_section = parts[0].replace("[ARABIC]", "").strip()
            english_section = parts[1].strip() if len(parts) > 1 else ""
        else:
            arabic_section = enhanced_text
            english_section = enhanced_text
        
        return jsonify({
            'success': True,
            'enhanced_arabic': arabic_section,
            'enhanced_english': english_section,
            'original_title': title
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<int:file_id>/summarize', methods=['POST'])
def summarize_file(file_id):
    """AI file summarization in both languages"""
    if not ai_configured:
        return jsonify({'error': 'AI not configured'}), 503

    conn = sqlite3.connect('smart_dms.db')
    c = conn.cursor()
    c.execute('SELECT original_filename, content_text FROM files WHERE id = ?', (file_id,))
    result = c.fetchone()
    conn.close()

    if not result:
        return jsonify({'error': 'File not found'}), 404

    filename, content = result
    
    if not content:
        return jsonify({'error': 'No text content'}), 400

    try:
        preview = content[:8000]
        prompt = f"""Professional summary of document '{filename}' in BOTH languages.

Requirements:
- Provide summary in Arabic and English
- Be professional and eloquent
- Highlight key points
- Max 250 words per language

Document:
{preview}

Format:
[ARABIC SUMMARY]
<summary in Arabic>

[ENGLISH SUMMARY]
<summary in English>
"""
        
        return jsonify({'success': True, 'summary': run_agent_task(prompt), 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    print("[STARTING] Smart DMS Starting...")
    print(f"[UPLOADS] Folder: {app.config['UPLOAD_FOLDER']}")
    print(f"[AI] Status: {'Enabled' if ai_configured else 'Disabled'}")
    print(f"[SERVER] Open your browser at: http://localhost:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)
