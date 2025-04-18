# app.py (Google API 요청/응답 형식을 최대한 따르는 - 안정 버전)

import os
import requests
import json
from flask import Flask, request, jsonify, make_response
import traceback # 오류 로깅 위해 추가

app = Flask(__name__)
# 한글 처리 및 JSON 출력 관련 설정 (선택 사항)
app.json.sort_keys = False # 키 순서 유지 (디버깅 시 유용)
app.json.ensure_ascii = False # 한글 깨짐 방지 원하시면 주석 해제

# URL 경로에서 모델 ID와 메서드 이름을 받음
# 예: /models/gemini-pro:generateContent -> model_id_with_method = "gemini-pro:generateContent"
@app.route('/models/<path:model_id_with_method>', methods=['POST'])
def gemini_proxy(model_id_with_method):

    # 1. 클라이언트로부터 Google API 요청 본문 받기
    google_api_payload = request.get_json()

    # 간단한 유효성 검사 (객체 형태이고 contents 포함 여부)
    if not google_api_payload or not isinstance(google_api_payload, dict) or 'contents' not in google_api_payload:
        return jsonify({"error": "Request body must be a valid JSON object containing 'contents'"}), 400

    print(f"요청 받은 모델/메서드: {model_id_with_method}")
    print(f"요청 받은 페이로드 (일부): {str(google_api_payload)[:200]}...") # 로그 길이 제한

    # 2. 환경 변수에서 API 키 읽기
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return jsonify({"error": {"code": 400, "message": "API key not configured on proxy server.", "status": "INVALID_ARGUMENT"}}), 400

    # 3. Google Gemini API 호출
    try:
        # URL 경로에서 받은 모델/메서드 정보와 API 키를 사용하여 실제 Google API URL 생성
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id_with_method}?key={gemini_api_key}"
        headers = { "Content-Type": "application/json" }

        # 클라이언트로부터 받은 페이로드 전체를 그대로 전달
        data_to_send = google_api_payload

        print(f"Google API 호출 시작: {api_url.split('key=')[0]}key=AIza...") # API 키 일부 숨김
        google_response = requests.post(api_url, headers=headers, json=data_to_send) # !!! 이 라인이 중요 !!!

        # 4. Google API 응답을 클라이언트에게 그대로 전달
        print(f"Google API 응답 상태 코드: {google_response.status_code}")
        response_content_type = google_response.headers.get('Content-Type', 'application/json')

        try:
            response_data = google_response.json()
            print("Google API 응답 (JSON 파싱 성공)")
        except json.JSONDecodeError:
            response_data = google_response.text # JSON 아니면 텍스트로 전달
            print("Google API 응답 (JSON 파싱 실패, 텍스트로 처리)")

        # Flask 응답 생성 (Google의 상태 코드와 내용 반영)
        response_to_client = make_response(jsonify(response_data) if isinstance(response_data, dict) else response_data, google_response.status_code)
        response_to_client.headers['Content-Type'] = response_content_type
        return response_to_client

    except requests.exceptions.RequestException as e:
        # 네트워크 오류 등 requests 자체 오류
        print(f"Error calling Google API: {e}")
        return jsonify({"error": "Proxy failed to call Google API", "details": str(e)}), 502 # Bad Gateway

    except Exception as e:
        # 기타 서버 내부 오류
        print(f"Internal server error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal proxy server error", "details": str(e)}), 500

# if __name__ == '__main__':
#     # Render 환경에서는 PORT 환경 변수를 사용하므로 app.run 불필요 (Gunicorn이 처리)
#     pass
