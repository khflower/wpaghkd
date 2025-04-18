# app.py (Google AI Python SDK 사용 - 기본 버전)

import os
import google.generativeai as genai # SDK import
from flask import Flask, request, jsonify
import traceback # 상세 오류 로깅을 위해 추가

app = Flask(__name__)
# app.json.ensure_ascii = False # 필요 시 주석 해제

# URL 경로에서 모델 식별자만 받음
@app.route('/models/<model_identifier>', methods=['POST'])
def gemini_proxy_sdk(model_identifier):

    client_payload = request.get_json()

    if not client_payload or not isinstance(client_payload, dict) or 'contents' not in client_payload:
        return jsonify({"error": "Request body must be a valid JSON object containing 'contents'"}), 400

    print(f"요청 받은 모델: {model_identifier}")
    print(f"요청 받은 페이로드 (일부): {str(client_payload)[:200]}...")

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return jsonify({"error": {"code": 400, "message": "API key not configured on proxy server.", "status": "INVALID_ARGUMENT"}}), 400

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_identifier)

        print(f"Gemini SDK 호출 시작 (모델: {model_identifier})")

        # SDK 호출 (클라이언트 페이로드의 키들을 인자로 사용)
        # generation_config, safety_settings 등은 클라이언트가 보내는대로 전달 시도
        sdk_response = model.generate_content(
            contents=client_payload.get('contents'),
            generation_config=client_payload.get('generationConfig'), # 클라이언트가 보내면 전달
            safety_settings=client_payload.get('safetySettings')      # 클라이언트가 보내면 전달
        )

        # 응답 텍스트 추출 및 반환
        generated_text = sdk_response.text
        print(f"Gemini SDK 응답 텍스트 (일부): {generated_text[:100]}...")
        return jsonify({"response": generated_text})

    except Exception as e:
        print(f"Error during Gemini SDK call or processing: {e}")
        traceback.print_exc()
        # 오류 응답 형식은 필요에 따라 상세화 가능
        return jsonify({"error": "Error generating content via proxy", "details": str(e)}), 500

# if __name__ == '__main__':
#     pass
