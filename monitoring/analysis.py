"""Traffic class analysis with retained violation-evidence logging."""
import time
from pathlib import Path

import cv2
from django.core.files.base import ContentFile

VEHICLE_CLASSES = {0: "person", 2: "car", 3: "motorcycle", 5: "bus"}
CONFIDENCE = .35
SAMPLE_LIMIT = 48
_vehicle_model = _helmet_model = None


class AnalysisError(Exception):
    pass


def _load_models():
    global _vehicle_model, _helmet_model
    try:
        from ultralytics import YOLO
        if _vehicle_model is None:
            _vehicle_model = YOLO("yolo11n.pt")
        if _helmet_model is None:
            _helmet_model = YOLO("helmet_violation.pt")
        return _vehicle_model, _helmet_model
    except Exception as exc:
        raise AnalysisError("Traffic or helmet model could not be loaded. Ensure yolo11n.pt and helmet_violation.pt are present.") from exc


def _traffic_level(score):
    return "Heavy" if score >= 70 else "Medium" if score >= 40 else "Low"


def _draw_box(image, coords, label, color, confidence):
    x1, y1, x2, y2 = map(int, coords)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
    text = f"{label} {confidence:.0%}"
    cv2.putText(image, text, (x1, max(22, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX, .6, color, 2)


def annotate_frame(frame):
    """Return accepted traffic counts and evidence triggers for one frame."""
    vehicle_model, helmet_model = _load_models()
    vehicle_result = vehicle_model(frame, verbose=False, conf=CONFIDENCE)[0]
    helmet_result = helmet_model(frame, verbose=False, conf=CONFIDENCE)[0]
    image = frame.copy()
    counts = {name: 0 for name in VEHICLE_CLASSES.values()}
    no_helmet = 0
    if vehicle_result.boxes is not None:
        for coords, class_id, confidence in zip(vehicle_result.boxes.xyxy.tolist(), vehicle_result.boxes.cls.int().tolist(), vehicle_result.boxes.conf.tolist()):
            name = VEHICLE_CLASSES.get(class_id, "car")
            counts[name] += 1
            _draw_box(image, coords, name, (0, 190, 0), confidence)
    if helmet_result.boxes is not None:
        for coords, class_id, confidence in zip(helmet_result.boxes.xyxy.tolist(), helmet_result.boxes.cls.int().tolist(), helmet_result.boxes.conf.tolist()):
            label = str(helmet_model.names[class_id])
            normalized_label = label.lower().replace("-", "_").replace(" ", "_")
            if normalized_label in {"no_helmet", "without_helmet", "nohelmet"}:
                no_helmet += 1
                _draw_box(image, coords, "NO HELMET", (0, 0, 255), confidence)
    return image, counts, no_helmet


def analyse_video(video):
    capture = cv2.VideoCapture(video.source.path)
    if not capture.isOpened():
        raise AnalysisError("OpenCV could not open this video file.")
    total_frames, fps = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)), capture.get(cv2.CAP_PROP_FPS) or 25
    if total_frames <= 0:
        capture.release(); raise AnalysisError("The video has no readable frames.")
    positions = sorted({int(i * (total_frames - 1) / max(SAMPLE_LIMIT - 1, 1)) for i in range(min(SAMPLE_LIMIT, total_frames))})
    peak, evidence_frames, best_frame, best_count = {name: 0 for name in VEHICLE_CLASSES.values()}, [], None, -1
    try:
        for position in positions:
            capture.set(cv2.CAP_PROP_POS_FRAMES, position); ok, frame = capture.read()
            if not ok: continue
            image, counts, violations = annotate_frame(frame)
            for name, value in counts.items(): peak[name] = max(peak[name], value)
            total = sum(counts.values())
            if total > best_count: best_frame, best_count = image, total
            if violations and len(evidence_frames) < 3:
                encoded, jpeg = cv2.imencode(".jpg", image)
                if encoded: evidence_frames.append((position / fps, jpeg.tobytes()))
    finally:
        capture.release()
    if best_frame is None: raise AnalysisError("No readable frames were found during analysis.")
    encoded, jpeg = cv2.imencode(".jpg", best_frame)
    if not encoded: raise AnalysisError("Could not create the annotated preview image.")
    video.preview.save(f"{Path(video.display_name).stem}-analysis.jpg", ContentFile(jpeg.tobytes()), save=False)
    average, visible = sum(peak.values()) / max(len(peak), 1), sum(peak.values())
    score = min(100.0, round(average * 10 + visible * 2, 2))
    return {"total_frames": total_frames, "vehicle_count": visible, "motorcycle_count": peak["motorcycle"], "car_count": peak["car"], "bus_count": peak["bus"], "person_count": peak["person"], "evidence_frames": evidence_frames, "summary": {"visible_vehicles": visible, "score": score, "level": _traffic_level(score)}}


def annotated_video_stream(video):
    capture = cv2.VideoCapture(video.source.path)
    if not capture.isOpened(): raise AnalysisError("OpenCV could not open this video file.")
    fps = capture.get(cv2.CAP_PROP_FPS) or 25
    try:
        while True:
            started = time.monotonic(); ok, frame = capture.read()
            if not ok: break
            image, _, _ = annotate_frame(frame)
            encoded, jpeg = cv2.imencode(".jpg", image)
            if encoded: yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
            remaining = 1 / fps - (time.monotonic() - started)
            if remaining > 0: time.sleep(remaining)
    finally:
        capture.release()
