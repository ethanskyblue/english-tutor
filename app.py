from flask import Flask, render_template, request, jsonify
import json
import urllib.request
import urllib.error
import os
import socket

app = Flask(__name__)

def load_api_key():
    key = os.environ.get('ANTHROPIC_API_KEY', '')
    if key and key != 'your_api_key_here':
        return key
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    if k.strip() == 'ANTHROPIC_API_KEY':
                        return v.strip()
    return ''

LEVEL_MAP = {
    'beginner': 'Beginner',
    'intermediate': 'Intermediate',
    'advanced': 'Advanced'
}
TOPIC_MAP = {
    'free': 'Free conversation',
    'travel': 'Travel',
    'food': 'Food',
    'work': 'Work / Business',
    'hobby': 'Hobbies',
    'shopping': 'Shopping'
}

def build_system(level, topic):
    return f"""You are a friendly and encouraging English conversation tutor.

Settings:
- Level: {LEVEL_MAP.get(level, 'Intermediate')}
- Topic: {TOPIC_MAP.get(topic, 'Free conversation')}

Your job:
1. Respond naturally in English to keep the conversation flowing
2. Gently correct grammar or expression errors if any
3. Suggest more natural alternatives when useful
4. If the user writes in Korean, encourage them to try in English and give a hint
5. Keep responses concise (2-4 sentences) and end with a follow-up question
6. Be warm, patient and encouraging

Respond ONLY with valid JSON (no markdown, no backticks):
{{"reply": "Your English response here", "feedback": "한국어로 교정/피드백 (없으면 빈 문자열)"}}

Level guidelines:
- Beginner: simple words, short sentences
- Intermediate: natural conversation, some idioms
- Advanced: complex expressions, nuanced feedback"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_ip')
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = '127.0.0.1'
    return jsonify({'ip': ip})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages', [])
    level = data.get('level', 'intermediate')
    topic = data.get('topic', 'free')

    api_key = load_api_key()
    if not api_key or api_key == 'your_api_key_here':
        return jsonify({'error': 'API 키가 설정되지 않았습니다. Railway 환경변수를 확인하세요.'}), 500

    payload = json.dumps({
        'model': 'claude-sonnet-4-6',
        'max_tokens': 1000,
        'system': build_system(level, topic),
        'messages': messages
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        raw = result['content'][0]['text']
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {'reply': raw, 'feedback': ''}
        return jsonify(parsed)

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            err_msg = json.loads(err_body).get('error', {}).get('message', err_body)
        except Exception:
            err_msg = err_body
        return jsonify({'error': f'API 오류 ({e.code}): {err_msg}'}), e.code

    except urllib.error.URLError as e:
        return jsonify({'error': f'네트워크 오류: {e.reason}'}), 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("English Tutor 웹앱 시작!")
    print(f"로컬 접속: http://localhost:{port}")
    print("종료: Ctrl+C")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
