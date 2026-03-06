import React, { useRef, useState } from "react";

function VideoAnalyzer() {
  const videoRef = useRef(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [detection, setDetection] = useState(null);

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  const handleVideoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoUrl(URL.createObjectURL(file));
    }
  };

  const startProcessing = () => {
    setInterval(() => processFrame(), 300);
  };

  const processFrame = async () => {
    const video = videoRef.current;
    if (!video) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append("file", blob, "frame.jpg");

      try {
        const res = await fetch("http://localhost:8000/video-frame", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        setDetection(data);
      } catch (err) {
        console.error("Error enviando frame:", err);
      }
    }, "image/jpeg");
  };

  return (
    <div>
      <h2>Analizador de Médico en Video</h2>

      <input type="file" accept="video/*" onChange={handleVideoUpload} />

      {videoUrl && (
        <div>
          <video
            ref={videoRef}
            src={videoUrl}
            width="500"
            controls
            onLoadedData={startProcessing}
          />

          <div style={{ marginTop: 20 }}>
            <h3>Resultado:</h3>
            {detection && (
              <>
                <p>Detectado: {detection.detected?.join(", ")}</p>
                <p>Faltante: {detection.missing?.join(", ")}</p>

                {detection.is_complete ? (
                  <p style={{ color: "green" }}>✔ Médico completo</p>
                ) : (
                  <p style={{ color: "red" }}>❌ Elementos faltantes</p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default VideoAnalyzer;
