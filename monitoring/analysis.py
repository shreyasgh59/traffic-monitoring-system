"""Bounded, local YOLO analysis used by the traffic-video queue."""

from pathlib import Path

import cv2
from django.core.files.base import ContentFile


VEHICLE_CLASSES = {2, 3, 5, 7}  # COCO: car, motorcycle, bus, truck
SAMPLE_LIMIT = 48
CONFIDENCE = 0.35
_model = None


class AnalysisError(Exception):
    pass


def _get_model():
    global _model
    if _model is None:
        try:
            from ultralytics import YOLO
            _model = YOLO("yolo11n.pt")
        except Exception as exc:
            raise AnalysisError(
                "YOLO weights could not be loaded. Connect to the internet once so Ultralytics can download yolo11n.pt."
            ) from exc
    return _model


def _traffic_level(score):
    if score >= 70:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def analyse_video(video):
    """Sample a clip, keep a representative annotated frame, and return metrics."""
    capture = cv2.VideoCapture(video.source.path)
    if not capture.isOpened():
        raise AnalysisError("OpenCV could not open this video file.")

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        capture.release()
        raise AnalysisError("The video has no readable frames.")

    positions = sorted({int(i * (total_frames - 1) / max(SAMPLE_LIMIT - 1, 1)) for i in range(min(SAMPLE_LIMIT, total_frames))})
    model = _get_model()
    counts = []
    best_frame = None
    best_count = -1
    try:
        for position in positions:
            capture.set(cv2.CAP_PROP_POS_FRAMES, position)
            ok, frame = capture.read()
            if not ok:
                continue
            result = model(frame, verbose=False, conf=CONFIDENCE)[0]
            class_ids = result.boxes.cls.int().tolist() if result.boxes is not None else []
            vehicle_count = sum(class_id in VEHICLE_CLASSES for class_id in class_ids)
            counts.append(vehicle_count)
            if vehicle_count > best_count:
                best_count = vehicle_count
                best_frame = result.plot()
    finally:
        capture.release()

    if not counts or best_frame is None:
        raise AnalysisError("No readable frames were found during analysis.")

    average = sum(counts) / len(counts)
    visible = max(counts)
    # This is a transparent density estimate, not a physical lane-coverage measurement.
    occupancy = min(100.0, round(average * 8.0, 2))
    score = min(100.0, round((average * 10.0) + (visible * 2.0), 2))
    encoded, image = cv2.imencode(".jpg", best_frame)
    if not encoded:
        raise AnalysisError("Could not create the annotated preview image.")

    preview_name = f"{Path(video.display_name).stem}-analysis.jpg"
    video.preview.save(preview_name, ContentFile(image.tobytes()), save=False)
    return {
        "summary": {
            "visible_vehicles": visible,
            "occupancy": occupancy,
            "score": score,
            "level": _traffic_level(score),
        }
    }
