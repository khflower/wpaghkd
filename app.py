# app.py (gemini-2.5-pro-exp-03-25 모델 사용 버전)

import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/gemini-proxy', methods=['POST'])
def gemini_proxy():
    # 1. 클라이언트 데이터 받기
    client_data = request.get_json()
    if not client_data or 'prompt' not in client_data:
        return jsonify({"error": "요청 본문에 'prompt' 키가 포함된 JSON 데이터가 필요합니다."}), 400

    user_prompt = client_data['prompt']
    print(f"요청 받음 (프롬프트): {user_prompt}")

    # 2. 환경 변수에서 API 키 읽기
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return jsonify({"error": "서버 설정 오류: API 키 없음"}), 500

    # 3. Google Gemini API 호출
    try:
        # Gemini API 엔드포인트 (v1beta, 요청하신 모델 사용)
        # !!! 여기가 변경된 부분입니다 !!!
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent?key={gemini_api_key}"

        # API 요청 헤더
        headers = {
            "Content-Type": "application/json"
        }

        # API 요청 본문 (Gemini API 형식에 맞게 구성)
        data = {
            "contents": [{
                "parts": [{
                    "text": user_prompt
                }]
            }]
            # 필요하다면 여기에 generationConfig 등 다른 파라미터 추가
        }

        # POST 요청 보내기
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status() # 오류 발생 시 예외 발생

        # 4. API 응답 처리 및 클라이언트에 반환
        gemini_response = response.json()

        # 응답 구조에서 실제 텍스트 추출 (일반적인 구조 가)
        generated_text = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '응답 텍스트를 추출하지 못했습니다.')

        print(f"Gemini 응답 (일부): {generated_text[:100]}...")

        return jsonify({"response": generated_text})

    except requests.exceptions.RequestException as e:
        print(f"Gemini API 호출 오류: {e}")
        error_details = "알 수 없는 오류"
        if e.response is not None:
            try:
                error_details = e.response.json()
            except ValueError: # 응답이 JSON이 아닐 경우
                error_details = e.response.text
        return jsonify({"error": "Gemini API 호출 중 오류 발생", "details": error_details}), 502

    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": "서버 내부 오류 발생"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
