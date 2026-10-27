from typing import List, Dict, Any

import cv2
import numpy as np

from facial_recognition import facial_recognition


def detect_faces(frame_bgr: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect faces in a single video frame.

    Returns a list of dicts, each containing at minimum:
        - 'bbox': (x1, y1, x2, y2) in pixel coordinates
        - 'confidence': float in [0, 1] (if available)
        - 'face_rgb': cropped face image (RGB) suitable for embedding
    """
    # Important: your existing pipeline historically passed the OpenCV frame
    # directly into `extract_faces_from_frame` (without BGR->RGB conversion).
    # Keeping the same color convention avoids "No face detected" failures.
    #
    # We assume extract_faces_from_frame returns a list of dicts with keys:
    #   - 'face': cropped RGB image
    #   - 'bbox': (x1, y1, x2, y2) or similar
    #   - 'confidence' (optional)
    raw_faces = facial_recognition.extract_faces_from_frame(frame_bgr)

    detections: List[Dict[str, Any]] = []
    for f in raw_faces:
        face_img = f.get("face")
        if face_img is None:
            continue

        bbox = f.get("bbox")
        # DeepFace typically returns `facial_area` rather than `bbox`.
        if bbox is None:
            facial_area = f.get("facial_area") or {}
            if all(k in facial_area for k in ("x", "y", "w", "h")):
                x = float(facial_area["x"])
                y = float(facial_area["y"])
                w = float(facial_area["w"])
                h = float(facial_area["h"])
                bbox = (x, y, x + w, y + h)

        # Some extractors may already provide explicit corner coordinates.
        if bbox is None and all(k in f for k in ("x1", "y1", "x2", "y2")):
            bbox = (f["x1"], f["y1"], f["x2"], f["y2"])

        # Fallback: if bbox not provided, approximate full frame (not ideal but safe)
        if bbox is None:
            h, w = frame_bgr.shape[:2]
            bbox = (0.0, 0.0, float(w), float(h))

        detections.append(
            {
                "bbox": bbox,
                "confidence": float(f.get("confidence", 1.0)),
                "face_rgb": face_img,
            }
        )

    return detections


def draw_detections(
    frame_bgr: np.ndarray,
    tracked_faces: List[Dict[str, Any]],
) -> np.ndarray:
    """
    Draw bounding boxes and labels on a frame for visualization.

    Each item in tracked_faces should contain:
        - 'track_id'
        - 'bbox': (x1, y1, x2, y2)
        - 'label': e.g. person's name or 'Unknown'
        - 'confidence': similarity score in [0, 1] (optional)
        - 'is_match': bool, True if known match
    """
    for t in tracked_faces:
        x1, y1, x2, y2 = [int(v) for v in t["bbox"]]
        is_match = bool(t.get("is_match", False))
        color = (0, 255, 0) if is_match else (0, 0, 255)  # green for match, red for unknown

        cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), color, 2)

        label = t.get("label", "Unknown")
        conf = t.get("confidence")
        if conf is not None:
            label_text = f"{label} ({conf:.2f})"
        else:
            label_text = label

        cv2.putText(
            frame_bgr,
            label_text,
            (x1, max(0, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
            cv2.LINE_AA,
        )

    return frame_bgr

