import React, { useRef, useEffect, useState } from "react";

function LiveCameraAnalyzer() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    startCamera();

    const interval = setInterval(() => {
      sendFrame();
    }, 300); // cada 300 ms (3 FPS)
    return () => clearInterval(interval);
  }, []);

  const startCamera = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false,
    });
    videoRef.current.srcObject = stream;
  };

  // Captura frame y lo envía al backend
  const sendFrame = () => {
    const video = videoRef.current;
    if (!video || video.readyState !== 4) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append("file", blob, "frame.jpg");

      try {
        const res = await fetch("http://127.0.0.1:8000/video-frame", {
          method: "POST",
          body: formData,
        });

        const json = await res.json();
        setData(json);

        drawBoxes(json.boxes);
      } catch (error) {
        console.error("Error:", error);
      }
    }, "image/jpeg");
  };

  // Dibuja cajas en tiempo real
  const drawBoxes = (boxes) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const video = videoRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!boxes) return;

    boxes.forEach((box) => {
      const [x1, y1, x2, y2] = box.bbox;

      ctx.strokeStyle = "#00FF00";
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

      ctx.font = "18px Arial";
      ctx.fillStyle = "#00FF00";
      ctx.fillText(
        `${box.class} (${(box.confidence * 100).toFixed(1)}%)`,
        x1,
        y1 - 5
      );
    });
  };

  return (
    <div style={{ position: "relative", width: 640, height: 480 }}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        width={640}
        height={480}
        style={{ position: "absolute", top: 0, left: 0 }}
      />

      <canvas
        ref={canvasRef}
        width={640}
        height={480}
        style={{ position: "absolute", top: 0, left: 0 }}
      />

      <div style={{ marginTop: 20 }}>
        <h3>Detección en tiempo real</h3>

        {data && (
          <>
            <p><b>Detectado:</b> {data.detected.join(", ")}</p>
            <p><b>Faltantes:</b> {data.missing.join(", ")}</p>
            {data.is_complete ? (
              <p style={{ color: "green" }}>✔ Médico completo</p>
            ) : (
              <p style={{ color: "red" }}>❌ Faltan elementos</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default LiveCameraAnalyzer;
