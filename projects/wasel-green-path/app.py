"""
واصل - الطريق الأخضر
Wasel Green Path - AI-Powered Sign Language Assistant
تطبيق ذكي لترجمة لغة الإشارة المصرية
"""

from flask import Flask, render_template, request, jsonify
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure AI - Support both Vertex AI (Service Account) and API Key
model = None
ai_method = "None"

# Option 1: Try Vertex AI with Service Account
service_account_path = os.path.join(os.path.dirname(__file__), 'service-account-key.json')
if os.path.exists(service_account_path):
    try:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        # Read project ID from service account file
        with open(service_account_path, 'r') as f:
            sa_data = json.load(f)
            project_id = sa_data.get('project_id', 'eg-konecta-sandbox')
        
        vertexai.init(project=project_id, location="us-central1")
        model = GenerativeModel("gemini-2.0-flash-001")
        
        # Initialize Imagen model
        from vertexai.preview.vision_models import ImageGenerationModel
        image_model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        ai_method = f"Vertex AI (Project: {project_id})"
        print(f"[✓] AI Configured: {ai_method}")
    except Exception as e:
        image_model = None
        print(f"[!] Vertex AI failed: {e}")
else:
    image_model = None

# Option 2: Fallback to API Key
if not model:
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if api_key and api_key != 'your_gemini_api_key_here':
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            ai_method = f"API Key (...{api_key[-4:]})"
            print(f"[✓] AI Configured: {ai_method}")
        except Exception as e:
            print(f"[!] API Key failed: {e}")

if not model:
    print("[!] Warning: No AI configured. Add service-account-key.json or set GEMINI_API_KEY")


# Load sign language dictionary
def load_dictionary():
    try:
        with open('sign_language_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"words": []}

# System prompt for sign language translation
SIGN_LANGUAGE_PROMPT = """
أنت مترجم خبير في لغة الإشارة المصرية (Egyptian Sign Language - ESL).
مهمتك هي تحويل النص العربي إلى وصف تفصيلي لحركات لغة الإشارة.

عند الترجمة، قدم:
1. **الكلمات الأساسية**: حدد الكلمات المفتاحية في الجملة
2. **وصف الإشارة**: صف حركة اليد والأصابع بدقة
3. **تعبيرات الوجه**: حدد التعبير المطلوب (ابتسامة، استفهام، تعجب)
4. **اتجاه الحركة**: من أين إلى أين تتحرك اليد

قواعد مهمة:
- لغة الإشارة تستخدم ترتيب مختلف عن العربية (الفعل غالباً في النهاية)
- التعبيرات الوجهية جزء أساسي من المعنى
- بعض الكلمات لها إشارة واحدة تعبر عن معانٍ متعددة

قدم الإجابة بتنسيق واضح ومرتب.
"""

DEAF_ASSISTANT_PROMPT = """
أنت مساعد ذكي متخصص في خدمة الأشخاص الصم وضعاف السمع في مصر.
مهمتك:
1. الرد بلغة بسيطة وواضحة (لغة سهلة القراءة).
2. تقديم معلومات مفيدة عن الخدمات المتاحة للصم.
3. **في حالات الطوارئ (نجدة، مساعدة، حادث، خطر):**
   - وجه المستخدم فوراً للضغط على زر **"شارك موقعك" (Share Location)** الموجود في شريط الطوارئ أعلى التطبيق.
   - وضح له أن هذا الزر سيسمح للمسؤولين بمعرفة مكانه بدقة للتدخل السريع.
   - ابق معه وطمئنه حتى يحصل على المساعدة.
4. الإجابة عن أي استفسارات بطريقة مختصرة وداعمة.

كن ودوداً ومتعاطفاً جداً، واستخدم الرموز التعبيرية لتوضيح المشاعر.
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/translate', methods=['POST'])
def translate_to_sign():
    """Translate text to sign language description"""
    if not model:
        return jsonify({'error': 'AI not configured'}), 500
    
    text = request.json.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        prompt = f"{SIGN_LANGUAGE_PROMPT}\n\nالنص المطلوب ترجمته:\n{text}"
        response = model.generate_content(prompt)
        
        return jsonify({
            'success': True,
            'original': text,
            'translation': response.text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with AI assistant for deaf community"""
    if not model:
        return jsonify({'error': 'AI not configured'}), 500
    
    message = request.json.get('message', '')
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        prompt = f"{DEAF_ASSISTANT_PROMPT}\n\nرسالة المستخدم:\n{message}"
        response = model.generate_content(prompt)
        
        return jsonify({
            'success': True,
            'response': response.text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dictionary')
def get_dictionary():
    """Get sign language dictionary"""
    dictionary = load_dictionary()
    search = request.args.get('search', '').lower()
    
    if search:
        filtered = [w for w in dictionary.get('words', []) 
                   if search in w.get('word', '').lower() or 
                      search in w.get('word_en', '').lower()]
        return jsonify({'words': filtered})
    
    return jsonify(dictionary)

@app.route('/api/emergency')
def get_emergency_phrases():
    """Get emergency sign language phrases"""
    dictionary = load_dictionary()
    emergency = [w for w in dictionary.get('words', []) 
                if w.get('category') == 'emergency']
    return jsonify({'phrases': emergency})

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'ai_configured': model is not None,
        'app': 'Wasel Green Path'
    })

@app.route('/api/generate-image', methods=['POST'])
def generate_sign_image():
    """Generate AI image for sign language and optionally save to dictionary"""
    if not model:
        return jsonify({'error': 'AI not configured'}), 500
    
    data = request.json
    word = data.get('word', '')
    description = data.get('description', '')
    save_to_dict = data.get('save', False)
    
    if not word or not description:
        return jsonify({'error': 'Missing word or description'}), 400
    
    try:
        # Generate image prompt
        prompt = f"""
        Educational illustration for sign language word: {word}. 
        Instructional gesture details: {description}.
        
        Style requirements:
        - Frontal view of hands and torso
        - Clean solid background
        - High contrast, professional drawing style
        - Arabic text "{word}" clearly visible at the top
        """
        
        # Use simple filename based on word
        safe_word = word.replace(' ', '_')
        image_relative_path = f"static/signs/{safe_word}.png"
        image_absolute_path = os.path.join(os.path.dirname(__file__), image_relative_path)
        
        # Create directory if doesn't exist
        os.makedirs(os.path.dirname(image_absolute_path), exist_ok=True)
        
        response_data = {
            'success': True,
            'word': word,
            'description': description
        }
        
        # Real image generation if image_model is available
        if 'image_model' in globals() and image_model:
            print(f"[AI] Generating image for: {word}")
            images = image_model.generate_images(
                prompt=prompt,
                number_of_images=1,
                language="ar", # Support for Arabic text in prompt
            )
            images[0].save(location=image_absolute_path, include_generation_parameters=False)
            response_data['image_url'] = f"/{image_relative_path}"
            response_data['message'] = f'✅ تم توليد وتحديث صورة الكلمة: {word}'
        else:
            response_data['note'] = 'Imagen API not initialized in this session'
            response_data['message'] = f'طلب توليد صورة للكلمة: {word} (محاكاة)'
        
        # Update/Save to dictionary
        dictionary = load_dictionary()
        existing = next((w for w in dictionary.get('words', []) if w.get('word') == word), None)
        
        if existing:
            # Update existing entry with new image
            if 'image_url' in response_data:
                existing['media_url'] = response_data['image_url']
                existing['media_type'] = 'image'
            response_data['saved'] = True
        elif save_to_dict:
            # Create new entry
            new_word = {
                'word': word,
                'word_en': data.get('word_en', word),
                'category': 'custom',
                'sign_description': description,
                'facial_expression': data.get('facial', 'تعبير محايد'),
                'hand_shape': data.get('hand_shape', 'حسب الوصف'),
                'movement': data.get('movement', 'حسب الوصف'),
                'media_type': 'image' if 'image_url' in response_data else None,
                'media_url': response_data.get('image_url')
            }
            dictionary['words'].append(new_word)
            response_data['saved'] = True
        
        # Save dictionary if any changes made
        if response_data.get('saved'):
            with open('sign_language_data.json', 'w', encoding='utf-8') as f:
                json.dump(dictionary, f, ensure_ascii=False, indent=4)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[!] Image Generation failed: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*50)
    print("🤟 واصل - الطريق الأخضر")
    print("   Wasel Green Path - AI Sign Language Assistant")
    print("="*50)
    print(f"[SERVER] Running on: http://localhost:{port}")
    print(f"[AI] Status: {'✓ Enabled' if model else '✗ Disabled'}")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=port)
