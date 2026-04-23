from flask import Flask, render_template, request, jsonify
import json
import urllib.request
import urllib.error
import os
import re

app = Flask(__name__)

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
    """API 키에서 불필요한 문자 완전 제거"""
    # 공백, 줄바꿈, 탭, 보이지 않는 유니코드 문자 모두 제거
    cleaned = re.sub(r'[\s\u200B\uFEFF\u00A0\u200C\u200D\u2060]+', '', raw)
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

    # 디버그용: 키 앞 12자리만 로그 출력 (Railway 로그에서 확인 가능)
    print(f"[DEBUG] key_raw_len={len(raw_key)} key_clean_len={len(api_key)} key_prefix={api_key[:12] if api_key else 'EMPTY'}")

    if not api_key:
        return jsonify({'error': 'API 키가 전달되지 않았습니다. ⚙️ 버튼을 눌러 키를 다시 설정해주세요.'}), 401

    # sk- 로 시작하는지만 확인 (sk-ant- 외 다른 형식도 허용)
    if not api_key.startswith('sk-'):
        return jsonify({'error': f'API 키 형식 오류. 받은 값 앞 6자리: [{api_key[:6]}]'}), 401

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
