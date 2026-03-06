from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import easyocr
import numpy as np
import io, base64, os, cv2, re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "diplomas-3/runs/detect/bachiller_v3/weights/best.pt")
model = YOLO(MODEL_PATH)

print("CLASES MODELO:", model.names)

reader = easyocr.Reader(['es'], gpu=False)

# Clases reales del modelo (automático)
YOLO_CLASSES = list(model.names.values())

# Campos obligatorios
REQUIRED_ITEMS = [
    "diploma",
    "escudo",
    "firma",
    "nombre",
    "institucion",
    "bachillerato"
]

def normalize(text):
    text = text.upper()
    text = re.sub(r'\s+', ' ', text)
    return text


@app.post("/predict")
async def validar_bachiller(file: UploadFile = File(...)):

    img_bytes = await file.read()
    img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_np = np.array(img_pil)
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    # detección YOLO optimizada
    results = model.predict(img_pil, conf=0.15, imgsz=960, verbose=False)
    boxes = results[0].boxes

    detected = []
    extracted_data = {}

    certificado_crop = None

    # ---------- DETECCIÓN ----------
    for box in boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]

        detected.append(label)

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)
        draw.text((x1, y1 - 18), label, fill="lime", font=font)

        if label == "diploma":
            certificado_crop = img_np[y1:y2, x1:x2]

    print("DETECTADOS:", detected)

    # ---------- OCR SOLO DOCUMENTO ----------
    if certificado_crop is not None:

        gray = cv2.cvtColor(certificado_crop, cv2.COLOR_RGB2GRAY)
        gray = cv2.equalizeHist(gray)

        ocr_text = reader.readtext(gray, detail=0)
        full_text = normalize(" ".join(ocr_text))

        # validar bachillerato
        extracted_data["bachillerato"] = "BACHILLER" in full_text

        # validar institución
        claves = ["INSTITUCION", "COLEGIO", "INSTITUTO", "ESCUELA"]
        extracted_data["institucion"] = next(
            (c for c in claves if c in full_text),
            ""
        )

        # detectar nombre
        nombres = re.findall(r'\b[A-Z]{3,}\s[A-Z]{3,}(\s[A-Z]{3,})?\b', full_text)
        extracted_data["nombre"] = nombres[0] if nombres else ""

    else:
        extracted_data["bachillerato"] = False
        extracted_data["institucion"] = ""
        extracted_data["nombre"] = ""

    # ---------- VALIDACIÓN ----------
    missing = []

    for item in REQUIRED_ITEMS:

        # si es clase YOLO
        if item in YOLO_CLASSES:
            if item not in detected:
                missing.append(item)

        # si es dato OCR
        else:
            if not extracted_data.get(item):
                missing.append(item)

    # ---------- IMAGEN RESULTADO ----------
    buffer = io.BytesIO()
    img_pil.save(buffer, format="JPEG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return JSONResponse({
        "detected_items": detected,
        "missing_items": missing,
        "is_valid": len(missing) == 0,
        "data": extracted_data,
        "message": "🟢 Diploma válido" if not missing else "🔴 Diploma incompleto o inválido",
        "image_base64": img_base64
    })