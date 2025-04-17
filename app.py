# app.py (멀티턴 대화 지원 버전)

import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
# 한글 출력을 위해 추가 (선택 사항, 이전 답변 참고)
app.json.ensure_ascii = False

@app.route('/gemini-proxy', methods=['POST'])
def gemini_proxy():
    # 1. 클라이언트 데이터 받기 (이제 'history' 배열을 기대)
    client_data = request.get_json()
    # 'history' 키가 있고, 리스트 형태인지 확인
    if not client_data or 'history' not in client_data or not isinstance(client_data['history'], list):
        return jsonify({"error": "요청 본문에 'history' 키가 포함된 JSON 배열 데이터가 필요합니다."}), 400

    conversation_history = client_data['history']
    # 간단한 로그 출력 (마지막 사용자 메시지만)
    if conversation_history:
        print(f"요청 받음 (마지막 메시지): {conversation_history[-1].get('parts', [{}])[0].get('text', '')}")
    else:
         print("요청 받음 (빈 히스토리)")

    # 2. 환경 변수에서 API 키 읽기
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return jsonify({"error": "서버 설정 오류: API 키 없음"}), 500

    # 3. Google Gemini API 호출
    try:
        # 사용할 모델 엔드포인트 (이전과 동일)
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent?key={gemini_api_key}"
        headers = { "Content-Type": "application/json" }

        # API 요청 본문: 클라이언트로부터 받은 history 배열을 contents로 사용
        data = {
            "contents": conversation_history
            # 필요하다면 여기에 generationConfig 등 추가
        }

        # POST 요청 보내기
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()

        # 4. API 응답 처리 및 클라이언트에 반환
        gemini_response = response.json()
        generated_text = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '응답 텍스트를 추출하지 못했습니다.')

        print(f"Gemini 응답 (일부): {generated_text[:100]}...")

        # 클라이언트에게는 새로 생성된 Gemini 답변 텍스트만 반환
        return jsonify({"response": generated_text})

    except requests.exceptions.RequestException as e:
        print(f"Gemini API 호출 오류: {e}")
        error_details = "알 수 없는 오류"
        if e.response is not None:
            try:
                error_details = e.response.json()
            except ValueError:
                error_details = e.response.text
        return jsonify({"error": "Gemini API 호출 중 오류 발생", "details": error_details}), 502

    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": "서버 내부 오류 발생"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
