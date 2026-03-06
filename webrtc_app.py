from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaBlackhole
import av
import cv2
import numpy as np
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best.pt")  # o yolo11s entrenado

model = YOLO(MODEL_PATH)

REQUIRED = ["lab_coat", "stethoscope"]

pcs = set()  # para guardar conexiones WebRTC


class Offer(BaseModel):
    sdp: str
    type: str


class VideoTransformTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()

        # frame -> numpy BGR
        img = frame.to_ndarray(format="bgr24")
        h, w, _ = img.shape

        # YOLO sobre el frame
        results = model.predict(img, conf=0.25, verbose=False)
        boxes = results[0].boxes

        detected = []

        # Dibujar detecciones en verde
        if boxes is not None:
            for box in boxes:
                cls_id = int(box.cls)
                label = model.names[cls_id]
                detected.append(label)

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(
                    img,
                    label,
                    (x1, max(y1 - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

        # Calcular faltantes
        missing = [x for x in REQUIRED if x not in detected]

        # Si faltan elementos, dibujar recuadros BLANCOS en el centro
        if missing:
            x_center = w // 2 - 150
            y_center = h // 2 - 100
            y_offset = 0

            for item in missing:
                # Caja blanca
                top_left = (x_center, y_center + y_offset)
                bottom_right = (x_center + 300, y_center + 80 + y_offset)

                cv2.rectangle(img, top_left, bottom_right, (255, 255, 255), thickness=-1)
                cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), thickness=2)

                cv2.putText(
                    img,
                    f"FALTA: {item}",
                    (x_center + 20, y_center + 50 + y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                )

                y_offset += 100

        # Volver a frame de video
        new_frame = av.VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        return new_frame


@app.post("/offer")
async def offer(offer: Offer):
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            pc.addTrack(VideoTransformTrack(track))
        else:
            # ignorar audio u otros tracks
            bh = MediaBlackhole()
            bh.addTrack(track)

    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=offer.sdp, type=offer.type)
    )

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
