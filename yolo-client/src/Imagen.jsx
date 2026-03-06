import { useState, useRef } from "react";
import axios from "axios";

function Imagen() {
  const [imageFile, setImageFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const fileInputRef = useRef(null);

  // 👉 Abrir la cámara
  const openCamera = () => {
    fileInputRef.current.click();
  };

  // 👉 Guardar la foto tomada y mostrarla en pantalla
  const handleTakePhoto = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setImageFile(file);
    setPreview(URL.createObjectURL(file));
  };

  // 👉 Enviar la foto al backend
  const handleSubmit = async () => {
    if (!imageFile) {
      alert("Primero toma una foto, mi amor ❤️");
      return;
    }

    try {
      setLoading(true);
      setResult(null);

      const formData = new FormData();
      formData.append("file", imageFile);

      const response = await axios.post(
        "http://localhost:8000/predict",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setResult(response.data);
    } catch (error) {
      console.error(error);
      alert("Hubo un error procesando la foto 😢");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "30px", fontFamily: "Arial" }}>
      <h2>📸 Verificador SGVA con Cámara</h2>

      {/* BOTÓN PARA TOMAR LA FOTO */}
      <button
        onClick={openCamera}
        style={{
          background: "#007bff",
          color: "white",
          padding: "12px 20px",
          borderRadius: "8px",
          border: "none",
          cursor: "pointer",
          fontSize: "16px"
        }}
      >
        📷 Tomar Foto
      </button>

      {/* INPUT OCULTO QUE ACTIVA LA CÁMARA */}
      <input
        type="file"
        accept="image/*"
        capture="environment"
        ref={fileInputRef}
        onChange={handleTakePhoto}
        style={{ display: "none" }}
      />

      {/* PREVIEW DE LA FOTO */}
      {preview && (
        <div style={{ marginTop: "20px" }}>
          <h3>Foto tomada:</h3>
          <img
            src={preview}
            alt="captura"
            style={{
              width: "300px",
              borderRadius: "10px",
              border: "2px solid #ddd"
            }}
          />
        </div>
      )}

      {/* BOTÓN DE ANALIZAR */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          marginTop: "20px",
          padding: "12px 20px",
          background: loading ? "#999" : "#28a745",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: loading ? "not-allowed" : "pointer",
          fontSize: "16px"
        }}
      >
        {loading ? "Analizando..." : "🔍 Analizar"}
      </button>

      {/* RESULTADOS */}
      {result && (
        <div
          style={{
            marginTop: "25px",
            padding: "20px",
            borderRadius: "8px",
            border: "1px solid #ccc"
          }}
        >
          <h2>Resultado</h2>

          <p
            style={{
              color: result.is_fully_equipped ? "green" : "red",
              fontWeight: "bold"
            }}
          >
            {result.message}
          </p>

          <h3>Elementos detectados:</h3>
          {result.detected_items.length > 0 ? (
            <ul>
              {result.detected_items.map((item, i) => (
                <li key={i}>✅ {item}</li>
              ))}
            </ul>
          ) : (
            <p>🚫 No se detectó nada</p>
          )}

          {!result.is_fully_equipped && (
            <>
              <h3>Faltantes:</h3>
              <ul>
                {result.missing_items.map((item, i) => (
                  <li key={i}>❌ {item}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default Imagen;


