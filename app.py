from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import easyocr
import numpy as np
import io, base64, os, cv2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "runs/detect/certificados_prod/weights/best.pt")

MODEL_PATH = os.path.join(BASE_DIR, "yolo11n.pt")

model = YOLO(MODEL_PATH)
reader = easyocr.Reader(['es'], gpu=False)

# Clases YOLO reales
YOLO_CLASSES = ["certificado", "escudo_colombia", "firma"]

REQUIRED_ITEMS = [
    "certificado",
    "escudo_colombia",
    "firma",
    "nombre",
    "institucion",
    "titulo"
]

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    img_bytes = await file.read()
    img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_np = np.array(img_pil)
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    results = model.predict(img_pil, conf=0.25, imgsz=640, verbose=False)
    boxes = results[0].boxes

    detected = []
    extracted_data = {}

    certificado_crop = None

    # --- DETECCIÓN YOLO ---
    for box in boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]

        detected.append(label)

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)
        draw.text((x1, y1 - 18), label, fill="lime", font=font)

        if label == "certificado":
            certificado_crop = img_np[y1:y2, x1:x2]

    # --- OCR SOLO SOBRE EL CERTIFICADO ---
    if certificado_crop is not None:
        ocr_text = reader.readtext(certificado_crop, detail=0)
        full_text = " ".join(ocr_text).lower()

        # reglas simples (pueden mejorar)
        extracted_data["nombre"] = next((t for t in ocr_text if t.istitle()), "")
        extracted_data["institucion"] = "universidad" if "universidad" in full_text else ""
        extracted_data["titulo"] = "certificado" if "certifica" in full_text else ""

    # --- VALIDACIÓN FINAL ---
    missing = []
    for item in REQUIRED_ITEMS:
        if item in YOLO_CLASSES:
            if item not in detected:
                missing.append(item)
        else:
            if not extracted_data.get(item):
                missing.append(item)

    # Imagen a base64
    buffer = io.BytesIO()
    img_pil.save(buffer, format="JPEG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return JSONResponse({
        "detected_items": detected,
        "missing_items": missing,
        "is_valid": len(missing) == 0,
        "data": extracted_data,
        "message": "🟢 Certificado válido" if not missing else "🔴 Certificado incompleto",
        "image_base64": img_base64
    })