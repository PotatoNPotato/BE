# server.py

# ── 1. .env 파일 로드 ──
from dotenv import load_dotenv  
import os

# .env 파일에 정의된 환경변수들을 os.environ으로 로드
load_dotenv()  

# 2. 환경변수 읽어 오기
FIREBASE_CRED = os.getenv("FIREBASE_CRED")  # 예: /home/.../firebase-adminsdk.json
PORT          = int(os.getenv("PORT", 8000))  # .env에 없으면 기본 8000

# 3. uvicorn 직접 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",  # backend/main.py 의 app 객체
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
