# app.py (role 값 소문자 변환 기능 추가, thinkingConfig 제거)

import os
import requests
import json
from flask import Flask, request, jsonify, make_response
import traceback

app = Flask(__name__)
app.json.sort_keys = False
app.json.ensure_ascii = False # 한글 필요 시 주석 해제

@app.route('/models/<path:model_id_with_method>', methods=['POST'])
def gemini_proxy(model_id_with_method):

    google_api_payload = request.get_json()

    if not google_api_payload or not isinstance(google_api_payload, dict) or 'contents' not in google_api_payload:
        return jsonify({"error": "Request body must be a valid JSON object containing 'contents'"}), 400

    print(f"요청 받은 모델/메서드: {model_id_with_method}")
    print(f"요청 받은 페이로드 (원본): {str(google_api_payload)[:200]}...")

    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return jsonify({"error": {"code": 400, "message": "API key not configured on proxy server.", "status": "INVALID_ARGUMENT"}}), 400

    try:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id_with_method}?key={gemini_api_key}"
        headers = { "Content-Type": "application/json" }

        # 페이로드 복사 또는 직접 수정 준비
        data_to_send = google_api_payload # 요청받은 페이로드를 기준으로 함

        # ---!!! Role 값 소문자 변환 시작 !!!---
        if 'contents' in data_to_send and isinstance(data_to_send.get('contents'), list):
            print("Transforming roles to lowercase...")
            transformed_contents = []
            for message in data_to_send.get('contents', []):
                # 각 메시지가 딕셔너리이고 'role' 키를 가지고 있는지 확인
                if isinstance(message, dict) and 'role' in message:
                    # 원본 수정을 피하거나 필요에 따라 직접 수정: message.copy() 사용 또는 직접 수정
                    new_message = message # 직접 수정 방식 선택 (더 간결함)
                    original_role = new_message.get('role')
                    if original_role == 'USER':
                        new_message['role'] = 'user'
                    elif original_role == 'MODEL':
                        new_message['role'] = 'model'
                    # 다른 role 값은 변경하지 않음
                    transformed_contents.append(new_message) # 수정된 메시지 추가
                elif isinstance(message, dict):
                     # role이 없는 dict는 그냥 추가
                     transformed_contents.append(message)
                else:
                     # 리스트 안에 dict가 아닌 다른 타입이 있을 경우 경고 로그 (선택적)
                     print(f"Warning: Skipping non-dictionary item in contents during role transformation: {message}")
            # 변환된 contents로 교체 (만약 직접 수정했다면 이 줄은 필요 없음)
            # data_to_send['contents'] = transformed_contents # 직접 수정했으므로 이 줄은 불필요
        # ---!!! Role 값 소문자 변환 끝 !!!---

        # 이전에 테스트했던 thinkingConfig 강제 설정 로직은 제거됨

        print(f"Google API로 보낼 최종 페이로드 (role 수정됨): {str(data_to_send)[:200]}...")

        print(f"Google API 호출 시작: {api_url.split('key=')[0]}key=AIza...")
        google_response = requests.post(api_url, headers=headers, json=data_to_send) # 수정된 data_to_send 사용

        print(f"Google API 응답 상태 코드: {google_response.status_code}")
        response_content_type = google_response.headers.get('Content-Type', 'application/json')

        try:
            response_data = google_response.json()
            print("Google API 응답 (JSON 파싱 성공)")
        except json.JSONDecodeError:
            response_data = google_response.text
            print("Google API 응답 (JSON 파싱 실패, 텍스트로 처리)")

        response_to_client = make_response(jsonify(response_data) if isinstance(response_data, dict) else response_data, google_response.status_code)
        response_to_client.headers['Content-Type'] = response_content_type
        return response_to_client

    except requests.exceptions.RequestException as e:
        print(f"Error calling Google API: {e}")
        return jsonify({"error": "Proxy failed to call Google API", "details": str(e)}), 502

    except Exception as e:
        print(f"Internal server error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal proxy server error", "details": str(e)}), 500

# if __name__ == '__main__':
#     pass
