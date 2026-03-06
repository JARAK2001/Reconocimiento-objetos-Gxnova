from roboflow import Roboflow
import os
from dotenv import load_dotenv

load_dotenv()

# Se puede usar la API Key desde el archivo .env o directamente
api_key = os.getenv("ROBOFLOW_API_KEY", "CplZLZLyJprNGmW06dhx")

rf = Roboflow(api_key=api_key)
project = rf.workspace("jhoels-workspace").project("diplomas-a5gqs")
version = project.version(3)

# Descargar en formato yolov11
dataset = version.download("yolov11")

print(f"Dataset descargado en: {dataset.location}")
