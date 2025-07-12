# backend/analyze.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from tflite_runtime.interpreter import Interpreter
from PIL import Image
import numpy as np, librosa, io, os
from google.cloud import storage   

router = APIRouter()

# ── A) GCS에서 모델을 내려받아 로컬 임시파일에 저장하는 함수 ──
def download_model_from_gcs() -> str:
    bucket_name   = os.getenv("GCS_BUCKET")
    model_path    = os.getenv("GCS_MODEL_PATH")
    if not bucket_name or not model_path:
        raise RuntimeError("GCS_BUCKET 또는 GCS_MODEL_PATH가 설정되지 않았습니다.")

    client = storage.Client()  # GOOGLE_APPLICATION_CREDENTIALS를 사용
    bucket = client.bucket(bucket_name)
    blob   = bucket.blob(model_path)

    # 임시 디렉토리에 같은 이름의 파일로 저장
    local_file = os.path.join(tempfile.gettempdir(), os.path.basename(model_path))
    blob.download_to_filename(local_file)
    return local_file

# ── B) 앱 시작 시 한 번만 모델 다운로드 & 인터프리터 초기화 ──
_model_local_path = download_model_from_gcs()
interpreter = Interpreter(model_path=_model_local_path)
interpreter.allocate_tensors()
in_detail  = interpreter.get_input_details()[0]
out_detail = interpreter.get_output_details()[0]

@router.post("/sound")
async def analyze_sound(file: UploadFile = File(...)):
    """
    POST /analyze/sound
    - multipart/form-data 로 'file' 필드에 WAV 오디오 업로드
    - 백엔드에서 스펙트로그램으로 변환 후 모델 추론
    - {"category": "...", "confidence": ...} 반환
    """
    # 0) 파일 타입 체크
    if not file.content_type.startswith("audio/"):
        raise HTTPException(400, "오디오 파일(.wav)만 업로드해주세요")
    try:
        # 1) 파일 바이트 읽기
        data = await file.read()

        # 2) librosa 로 메모리상에서 WAV 로드
        y, sr = librosa.load(io.BytesIO(data), sr=22050)

        # 3) Mel Spectrogram 생성 (shape: [n_mels, time_frames])
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
        S_db = librosa.power_to_db(S, ref=np.max)

        # 4) Spectrogram 배열을 0~255 그레이스케일 이미지로 변환
        norm = (S_db - S_db.min()) / (S_db.max() - S_db.min())
        img = Image.fromarray((norm * 255).astype(np.uint8)) \
                   .resize((96, 96)) \
                   .convert("RGB")

        # 5) 모델 입력 형태로 변환 (1,96,96,3) & 정규화
        arr = np.array(img) / 255.0
        input_data = arr.astype(np.float32)[None, ...]

        # 6) TFLite 추론
        interpreter.set_tensor(in_detail["index"], input_data)
        interpreter.invoke()
        score = float(interpreter.get_tensor(out_detail["index"])[0][0])

        # 7) 결과 라벨링
        if score > 0.5:
            return {"category": "car_horn", "confidence": score}
        else:
            return {"category": "not_horn", "confidence": 1 - score}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추론 중 오류: {e}")