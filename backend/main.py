# ── backend/main.py ──

# 1. FastAPI 불러오기
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.analyze import router as analyze_router
# from backend.auth    import router as auth_router
from backend.history import router as history_router
# from backend.notification import router as notification_router

# 2. FastAPI 앱 객체 생성
app = FastAPI()

# prefix 주기
app.include_router(analyze_router, prefix="/analyze", tags=["AI Analysis"])
# app.include_router(auth_router,    prefix="/auth",    tags=["Authentication"])
app.include_router(history_router, prefix="/history", tags=["History"])
# app.include_router(notification_router, prefix="/notification",tags=["Notification"])

# 3. 헬스체크용 엔드포인트 정의
@app.get("/")
def health_check():
    """
    서버 체크 
    """
    return "Welcom To Backend Server"

