import { useRef, useState, useEffect } from "react";
import axios from "axios";

function CamaraMedica() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [outputImage, setOutputImage] = useState(null);
  const [loading, setLoading] = useState(false);

  // 🔹 Activar cámara al montar el componente
  useEffect(() => {
    startCamera();
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true, // En laptop usamos frontal
        audio: false,
      });

      videoRef.current.srcObject = stream;
      videoRef.current.play();
    } catch (error) {
      console.error("Error al acceder a la cámara:", error);
      alert("No se pudo acceder a la cámara");
    }
  };

  // 🔹 Tomar una foto desde el video
  const takePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    // Captura normal (NO afecta el transform visual)
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataURL = canvas.toDataURL("image/jpeg");
    setPreview(dataURL);
  };

  // 🔹 Enviar al backend
  const analyzePhoto = async () => {
    if (!preview) return alert("Primero toma una foto");

    setLoading(true);
    setResult(null);

    try {
      const blob = await fetch(preview).then((res) => res.blob());
      const file = new File([blob], "foto.jpg", { type: "image/jpeg" });

      const formData = new FormData();
      formData.append("file", file);

      const res = await axios.post("http://localhost:8000/predict", formData);

      setResult(res.data);
      setOutputImage("data:image/jpeg;base64," + res.data.image_base64);
    } catch (err) {
      console.error(err);
      alert("Error al analizar la imagen");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>🩺 SGVA – Validación Médica con Cámara</h1>

      {/* Cámara */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{
          width: "100%",
          maxWidth: "400px",
          borderRadius: "10px",
          border: "3px solid #666",
          transform: "scaleX(-1)" // 👈 Corrige efecto espejo en laptop
        }}
      />

      {/* Botón para tomar foto */}
      <button
        onClick={takePhoto}
        style={{
          padding: "12px 18px",
          marginTop: "10px",
          background: "#007bff",
          color: "white",
          borderRadius: "8px",
          border: "none",
          cursor: "pointer"
        }}
      >
        📸 Tomar foto
      </button>

      {/* Canvas oculto */}
      <canvas ref={canvasRef} style={{ display: "none" }} />

      {/* Vista previa */}
      {preview && (
        <div style={{ marginTop: 20 }}>
          <h3>📷 Foto tomada</h3>
          <img
            src={preview}
            alt="preview"
            style={{
              width: "300px",
              borderRadius: 10,
              border: "2px solid #ddd"
            }}
          />
        </div>
      )}

      {/* Botón analizar */}
      {preview && (
        <button
          onClick={analyzePhoto}
          disabled={loading}
          style={{
            padding: "12px 18px",
            marginTop: "10px",
            background: "#28a745",
            color: "white",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer"
          }}
        >
          {loading ? "Analizando..." : "🔍 Analizar imagen"}
        </button>
      )}

      {/* Imagen procesada */}
      {outputImage && (
        <div style={{ marginTop: 20 }}>
          <h3>🔎 Imagen procesada</h3>
          <img
            src={outputImage}
            alt="procesada"
            style={{
              width: "300px",
              borderRadius: 10,
              border: "2px solid #ddd"
            }}
          />
        </div>
      )}

      {/* Resultado */}
      {result && (
        <div style={{ marginTop: 20 }}>
          <h2>{result.message}</h2>

          <h3>Elementos detectados:</h3>
          <ul>
            {result.detected_items.map((item, idx) => (
              <li key={idx}>✔ {item}</li>
            ))}
          </ul>

          {result.missing_items.length > 0 && (
            <>
              <h3>Faltantes:</h3>
              <ul>
                {result.missing_items.map((item, idx) => (
                  <li key={idx}>❌ {item}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default CamaraMedica;