from flask import Flask, render_template, request, jsonify
import json
import urllib.request
import urllib.error
import os
import re

app = Flask(__name__)

def load_api_key():
    # 로컬 .env 파일 (개발용)
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

def build_system(level, topic):
    level_map = {
        'beginner': 'Beginner',
        'intermediate': 'Intermediate',
        'advanced': 'Advanced'
    }
    topic_map = {
        'free': 'Free conversation',
        'travel': 'Travel',
        'food': 'Food',
        'work': 'Work / Business',
        'hobby': 'Hobbies',
        'shopping': 'Shopping'
    }
    return f"""You are a friendly and encouraging English conversation tutor.

Settings:
- Level: {level_map.get(level, 'Intermediate')}
- Topic: {topic_map.get(topic, 'Free conversation')}

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

def clean_key(raw):
    """API 키에서 불필요한 문자 완전 제거 - ASCII 출력 가능 문자만 허용"""
    cleaned = ''.join(c for c in raw if 0x20 <= ord(c) <= 0x7E)
    return cleaned.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data     = request.get_json(force=True, silent=True) or {}
    messages = data.get('messages', [])
    level    = data.get('level', 'intermediate')
    topic    = data.get('topic', 'free')
    raw_key  = data.get('api_key', '')
    api_key  = clean_key(raw_key)

    print(f"[DEBUG] key_len={len(api_key)} key_prefix={api_key[:12] if api_key else 'EMPTY'}")

    if not api_key or len(api_key) < 20:
        return jsonify({'error': f'API 키가 올바르지 않습니다. (길이: {len(api_key)}자)'}), 401

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
        print(f"[DEBUG] HTTPError {e.code}: {err_body[:200]}")
        try:
            err_msg = json.loads(err_body).get('error', {}).get('message', err_body)
        except Exception:
            err_msg = err_body
        return jsonify({'error': f'API 오류 ({e.code}): {err_msg}'}), e.code

    except urllib.error.URLError as e:
        return jsonify({'error': f'네트워크 오류: {e.reason}'}), 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"서버 시작: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
