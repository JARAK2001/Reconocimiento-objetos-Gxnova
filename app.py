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

# Rutas de los modelos
# Modelo de certificados: usa el modelo entrenado por el compañero (train2)
MODEL_CERTIFICADO_PATH = os.path.join(BASE_DIR, "runs/detect/train2/weights/best.pt")
MODEL_DIPLOMA_PATH = os.path.join(BASE_DIR, "Diplomas-3/runs/detect/bachiller_v3/weights/best.pt")

# Cargamos ambos modelos en memoria al iniciar el servidor
model_certificado = YOLO(MODEL_CERTIFICADO_PATH)
model_diploma = YOLO(MODEL_DIPLOMA_PATH)

# Clases que YOLO puede detectar visualmente (de cada modelo)
YOLO_CLASSES_CERTIFICADO = list(model_certificado.names.values())
YOLO_CLASSES_DIPLOMA = list(model_diploma.names.values())

reader = easyocr.Reader(['es'], gpu=False)

# ---- REGLAS DE REQUERIMIENTOS ----
# Modelo del compañero (train2) detecta: curso, firma, institucion, margen, nombre
# Solo requerimos los que detecta de forma confiable:
REQUIRED_ITEMS_CERTIFICADO = ["curso", "firma", "institucion", "nombre"]
REQUIRED_ITEMS_DIPLOMA = ["diploma", "escudo"]

def normalize(text):
    text = text.upper()
    text = re.sub(r'\s+', ' ', text)
    return text

# ==============================================================================
# ENDPOINT 1: CERTIFICADOS
# ==============================================================================
@app.post("/predict/certificado")
async def predict_certificado(file: UploadFile = File(...)):
    img_bytes = await file.read()
    img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_np = np.array(img_pil)
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    results = model_certificado.predict(img_pil, conf=0.05, imgsz=640, verbose=False)
    boxes = results[0].boxes

    detected = []
    extracted_data = {}
    certificado_crop = None

    # --- DETECCIÓN YOLO ---
    for box in boxes:
        cls_id = int(box.cls[0])
        label = model_certificado.names[cls_id]
        conf_score = float(box.conf[0])
        detected.append(label)
        print(f"[CERTIFICADO] Detectado: {label} (conf={conf_score:.2f}")

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
    for item in REQUIRED_ITEMS_CERTIFICADO:
        if item in YOLO_CLASSES_CERTIFICADO:
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

# ==============================================================================
# ENDPOINT 2: DIPLOMAS DE BACHILLER
# ==============================================================================
@app.post("/predict/diploma")
async def predict_diploma(file: UploadFile = File(...)):
    img_bytes = await file.read()
    img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_np = np.array(img_pil)
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    # detección YOLO optimizada (conf reducido para debug)
    results = model_diploma.predict(img_pil, conf=0.05, imgsz=960, verbose=False)
    boxes = results[0].boxes

    detected = []
    extracted_data = {}
    certificado_crop = None

    # ---------- DETECCIÓN ----------
    for box in boxes:
        cls_id = int(box.cls[0])
        label = model_diploma.names[cls_id]
        conf_score = float(box.conf[0])
        detected.append(label)
        print(f"[DIPLOMA] Detectado: {label} (conf={conf_score:.2f})")

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)
        draw.text((x1, y1 - 18), label, fill="lime", font=font)

        if label == "diploma":
            certificado_crop = img_np[y1:y2, x1:x2]

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
    for item in REQUIRED_ITEMS_DIPLOMA:
        # si es clase YOLO
        if item in YOLO_CLASSES_DIPLOMA:
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