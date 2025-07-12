# ── backend/main.py ──

# 1. FastAPI 불러오기
from fastapi import FastAPI
from backend.analyze import router as analyze_router
# 2. FastAPI 앱 객체 생성
app = FastAPI()

# 3. 헬스체크용 엔드포인트 정의
@app.get("/")
def health_check():
    """
    서버 체크 
    """
    return "Welcom To Backend Server"