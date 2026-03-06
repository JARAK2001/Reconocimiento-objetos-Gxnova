import { useEffect, useRef, useState } from "react";
import axios from "axios";

function VideoDoctor() {
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const pcRef = useRef(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    start();
    return () => {
      if (pcRef.current) {
        pcRef.current.close();
      }
    };
  }, []);

  const start = async () => {
    try {
      // 1. Capturar cámara
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // 2. Crear PeerConnection
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });
      pcRef.current = pc;

      // 3. Enviar video local al backend
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      // 4. Recibir stream procesado
      pc.ontrack = (event) => {
        const [remoteStream] = event.streams;
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = remoteStream;
        }
      };

      // 5. Crear offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // 6. Enviar offer al backend
      const res = await axios.post("http://localhost:8000/offer", {
        sdp: offer.sdp,
        type: offer.type,
      });

      const answer = new RTCSessionDescription(res.data);
      await pc.setRemoteDescription(answer);

      setConnected(true);
    } catch (err) {
      console.error("Error iniciando WebRTC:", err);
      alert("No se pudo iniciar la cámara o la conexión.");
    }
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial" }}>
      <h1>🩺 Verificador SGVA en tiempo real (WebRTC)</h1>
      <p>
        Izquierda: video original · Derecha: video procesado (cajas verdes + recuadros blancos para faltantes).
      </p>

      <div style={{ display: "flex", gap: 20 }}>
        <div>
          <h3>📷 Cámara</h3>
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            style={{ width: 320, border: "2px solid #ccc", borderRadius: 8 }}
          />
        </div>

        <div>
          <h3>✅ Análisis SGVA</h3>
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            style={{ width: 320, border: "2px solid #4caf50", borderRadius: 8 }}
          />
        </div>
      </div>

      <p style={{ marginTop: 20 }}>
        Estado:{" "}
        <strong style={{ color: connected ? "green" : "red" }}>
          {connected ? "Conectado" : "Conectando..."}
        </strong>
      </p>
    </div>
  );
}

export default VideoDoctor;
