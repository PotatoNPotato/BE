# backend/history.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
import datetime
import os

# ── 1) APIRouter 객체 생성 ──
router = APIRouter()

# ── 2) DB 파일 경로 설정 ──
DB_PATH = os.path.join(os.path.dirname(__file__), "history.db")

# ── 3) SQLite 연결 & 테이블 생성 ──
#    check_same_thread=False 로 여러 요청 간 공유 가능
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    confidence REAL NOT NULL,
    timestamp TEXT NOT NULL
)
""")
conn.commit()

# ── 4) 요청 바디 모델 정의 ──
class LogItem(BaseModel):
    category: str       # ex) "car_horn", "doorbell"
    confidence: float   # 0.0 ~ 1.0 사이 확률

# ── 5) 이력 저장 엔드포인트 ──
@router.post("/log")
def add_log(item: LogItem):
    """
    POST /history/log
    - category: 분류된 소리 카테고리
    - confidence: 모델 확신도 (0~1)
    """
    ts = datetime.datetime.utcnow().isoformat()
    try:
        conn.execute(
            "INSERT INTO logs (category, confidence, timestamp) VALUES (?, ?, ?)",
            (item.category, item.confidence, ts)
        )
        conn.commit()
        return {"status": "ok", "timestamp": ts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── 6) 이력 조회 엔드포인트 ──
@router.get("/log")
def get_logs(limit: int = 50):
    """
    GET /history/log?limit=50
    - limit: 최근 몇 건을 조회할지 (기본 50)
    """
    try:
        cur = conn.execute(
            "SELECT category, confidence, timestamp FROM logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = [
            {"category": r[0], "confidence": r[1], "timestamp": r[2]}
            for r in cur.fetchall()
        ]
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
