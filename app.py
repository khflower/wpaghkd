# app.py

import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/gemini-proxy', methods=['POST'])
def gemini_proxy():
    client_data = request.get_json()
    if not client_data:
        return jsonify({"error": "요청 본문에 JSON 데이터가 없습니다."}), 400

    print(f"요청 받음: {client_data}")

    gemini_api_key = os.environ.get('GEMINI_API_KEY')

    if not gemini_api_key:
        print("오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        # 실제 운영에서는 아래처럼 에러를 반환해야 하지만, 지금은 키 존재 여부만 확인
        # return jsonify({"error": "서버 설정 오류: API 키 없음"}), 500
        print("API 키가 환경 변수에 없습니다. (실제 호출은 하지 않음)")

    # *** 나중에 여기에 Gemini API 호출 로직 추가 ***
    print(f"API Key (처음 5자리): {gemini_api_key[:5]}..." if gemini_api_key else "API Key 없음") # 디버깅용 (실제 키 전체 출력 X)

    return jsonify({
        "message": "요청 성공 (파이썬 프록시 - 기본)",
        "received_data": client_data
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True 추가 (개발 중 코드 변경 시 자동 재시작)
