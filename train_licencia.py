from ultralytics import YOLO
import os

def train_model():
    # Cargar el modelo base YOLOv11
    model = YOLO("yolo11s.pt")

    # Ruta al archivo data.yaml
    data_path = r"c:\Users\usuario\OneDrive\Documents\reconocimientoobjetos\My-First-Project-5\data.yaml"
    
    # Iniciar entrenamiento
    results = model.train(
        data=data_path,
        epochs=50,
        imgsz=640,
        plots=True,
        device='cpu',
        project=os.path.join(os.getcwd(), "reconocimientoobjetos", "runs") # Guardar en la carpeta correcta
    )
    
    print("Entrenamiento completado.")
    print(f"Mejor modelo guardado en: {results.save_dir}")

if __name__ == "__main__":
    train_model()
