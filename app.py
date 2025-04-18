# app.py (Google API 요청/응답 형식을 최대한 따르는 버전)

import os
import requests
import json # JSONDecodeError 처리를 위해 import
from flask import Flask, request, jsonify, make_response # make_response 추가

app = Flask(__name__)
# 한글 처리 및 JSON 출력 관련 설정 (선택 사항)
app.json.sort_keys = False # 키 순서 유지 (디버깅 시 유용)
app.json.ensure_ascii = False # 한글 깨짐 방지 (필요 시 주석 해제)

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
        # 실제 Google API가 키 없을 때 400 Bad Request를 반환하기도 함
        return jsonify({"error": {"code": 400, "message": "API key not configured on proxy server.", "status": "INVALID_ARGUMENT"}}), 400

    # 3. Google Gemini API 호출
    try:
        # URL 경로에서 받은 모델/메서드 정보와 API 키를 사용하여 실제 Google API URL 생성
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id_with_method}?key={gemini_api_key}"

        headers = { "Content-Type": "application/json" }

        # --- !!! 페이로드 수정: thinkingConfig 강제 설정 시작 !!! ---
        # google_api_payload를 직접 수정하거나, 복사본을 만들어도 됨
        # 여기서는 직접 수정하는 방식으로 진행
        data_to_send = google_api_payload

        # setdefault: 'generationConfig' 키가 없으면 빈 dict를 값으로 설정하고 반환, 있으면 기존 dict 반환
        gen_config = data_to_send.setdefault('generationConfig', {})
        # setdefault: 'thinkingConfig' 키가 없으면 빈 dict를 값으로 설정하고 반환, 있으면 기존 dict 반환
        think_config = gen_config.setdefault('thinkingConfig', {})
        # 'thinkingBudget' 값을 1024로 강제 설정 (기존 값이 있어도 덮어씀)
        think_config['thinkingBudget'] = 0
        # --- !!! 페이로드 수정: thinkingConfig 강제 설정 끝 !!! ---

        print(f"Google API로 보낼 최종 페이로드 (수정됨): {str(data_to_send)[:200]}...") # 수정된 페이로드 확인

        # Google API 호출 (수정된 data_to_send 사용)

        # 4. Google API 응답을 클라이언트에게 그대로 전달
        print(f"Google API 응답 상태 코드: {google_response.status_code}")

        # Google API 응답의 Content-Type 확인 및 설정
        response_content_type = google_response.headers.get('Content-Type', 'application/json')

        # 응답 본문 처리 (JSON 시도, 실패 시 텍스트)
        try:
            response_data = google_response.json()
            print("Google API 응답 (JSON 파싱 성공)")
        except json.JSONDecodeError:
            response_data = google_response.text # JSON 아니면 텍스트로 전달
            print("Google API 응답 (JSON 파싱 실패, 텍스트로 처리)")

        # Flask 응답 생성 (Google의 상태 코드와 내용 반영)
        # make_response를 사용하여 상태 코드와 헤더를 설정
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
        return jsonify({"error": "Internal proxy server error", "details": str(e)}), 500

if __name__ == '__main__':
    # Render 환경에서는 PORT 환경 변수를 사용하므로 app.run 불필요 (Gunicorn이 처리)
    # 로컬 테스트 시에는 아래 주석 해제 가능
    # app.run(host='0.0.0.0', port=5000, debug=True)
    pass # Gunicorn 사용 시 이 부분은 실행되지 않음
