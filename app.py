# app.py (Google API 요청 본문을 직접 받는 버전)

import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
# 한글 출력을 위해 추가 (선택 사항)
app.json.ensure_ascii = False

@app.route('/gemini-proxy', methods=['POST'])
def gemini_proxy():
    # 1. 클라이언트 데이터 받기 (Google API 요청 본문 전체를 기대)
    google_api_payload = request.get_json()

    # 받은 데이터가 유효한 JSON 객체이고 'contents' 키를 포함하는지 확인
    if not google_api_payload or not isinstance(google_api_payload, dict) or 'contents' not in google_api_payload:
        return jsonify({"error": "요청 본문은 'contents' 키를 포함하는 유효한 JSON 객체여야 합니다."}), 400

    # 간단한 로그 출력 (contents의 마지막 사용자 메시지)
    contents = google_api_payload.get('contents', [])
    if contents and isinstance(contents, list) and len(contents) > 0:
        last_message = contents[-1]
        if isinstance(last_message, dict):
             print(f"요청 받음 (마지막 메시지): {last_message.get('parts', [{}])[0].get('text', '')}")
    else:
         print("요청 받음 (contents 없음 또는 비정상)")


    # 2. 환경 변수에서 API 키 읽기
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return jsonify({"error": "서버 설정 오류: API 키 없음"}), 500

    # 3. Google Gemini API 호출
    try:
        # 사용할 모델 엔드포인트 (API 키를 URL 파라미터로 전달)
        # 모델 이름은 필요에 따라 변경 가능
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent?key={gemini_api_key}"
        headers = { "Content-Type": "application/json" }

        # API 요청 본문: 클라이언트로부터 받은 JSON 객체 전체를 그대로 사용
        data = google_api_payload

        # POST 요청 보내기
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status() # 오류 발생 시 예외 발생

        # 4. API 응답 처리 및 클라이언트에 반환
        gemini_response = response.json()

        # !!! 다음 줄을 추가하여 Google API의 전체 응답을 로그로 출력 !!!
        print(f"==== Google API 응답 전체 시작 ====")
        print(gemini_response)
        print(f"==== Google API 응답 전체 끝 ====")
    
        

        # 응답 구조에서 실제 텍스트 추출
        # (주의: 오류 응답 또는 응답 구조가 다를 경우를 대비한 추가 처리가 필요할 수 있음)
        generated_text = "응답 텍스트를 찾을 수 없습니다." # 기본값
        if 'candidates' in gemini_response and len(gemini_response['candidates']) > 0:
            candidate = gemini_response['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                generated_text = candidate['content']['parts'][0].get('text', generated_text)

        print(f"Gemini 응답 (일부): {generated_text[:100]}...")

        # 클라이언트에게는 최종 생성된 텍스트만 반환 (필요시 응답 구조 변경 가능)
        return jsonify({"response": generated_text})

    except requests.exceptions.RequestException as e:
        print(f"Gemini API 호출 오류: {e}")
        error_details = "알 수 없는 오류"
        if e.response is not None:
            try:
                error_details = e.response.json()
            except ValueError:
                error_details = e.response.text
        # 클라이언트에게 Google API의 오류 응답을 그대로 전달하거나 요약해서 전달할 수 있음
        # 예시: return jsonify({"error": "Gemini API 호출 오류", "details": error_details}), e.response.status_code if e.response is not None else 502
        return jsonify({"error": "Gemini API 호출 중 오류 발생", "details": error_details}), 502 # 이전과 동일하게 502 반환

    except Exception as e:
        print(f"서버 내부 오류: {e}")
        return jsonify({"error": "서버 내부 오류 발생"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
