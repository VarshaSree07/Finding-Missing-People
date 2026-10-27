import os
import uuid
from typing import Generator, Tuple, Optional

import cv2


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_video_file(file_storage, prefix: str = "video") -> str:
    """
    Save an uploaded video (Werkzeug FileStorage) to disk.

    Returns the absolute path to the saved file.
    """
    ext = os.path.splitext(file_storage.filename or "")[1] or ".mp4"
    filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(path)
    return path


def save_base64_video(data: str, prefix: str = "video") -> Optional[str]:
    """
    Save a base64 encoded video payload to disk.

    Returns the absolute path to the saved file or None on failure.
    """
    import base64

    try:
        if "," in data:
            data = data.split(",", 1)[1]
        raw = base64.b64decode(data)
        filename = f"{prefix}_{uuid.uuid4().hex}.mp4"
        path = os.path.join(UPLOAD_FOLDER, filename)
        with open(path, "wb") as f:
            f.write(raw)
        return path
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[video_processor] Failed to save base64 video: {exc}")
        return None


def _compute_frame_stride(cap: cv2.VideoCapture, target_fps: float) -> int:
    """
    Compute how many frames to skip to approximate target_fps.
    """
    if target_fps <= 0:
        return 1
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 0
    if src_fps <= 0:
        return 1
    stride = int(round(src_fps / target_fps))
    return max(stride, 1)


def iter_video_frames(
    video_path: str,
    target_fps: float = 1.0,
) -> Generator[Tuple[int, "np.ndarray"], None, None]:
    """
    Yield sampled frames from a video.

    Args:
        video_path: Path to the video file.
        target_fps: Approximate frames-per-second to process
                    (e.g. 1–5). We dynamically skip frames to achieve this.

    Yields:
        (frame_index, frame_bgr)
    """
    import numpy as np  # local import to keep module lightweight at import time

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video file: {video_path}")

    stride = _compute_frame_stride(cap, target_fps)
    frame_index = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_index % stride == 0:
                # Defensive copy so downstream modifications don't affect OpenCV buffer
                yield frame_index, frame.copy()

            frame_index += 1
    finally:
        cap.release()


def iter_webcam_frames(
    source: int | str = 0,
    target_fps: float = 5.0,
) -> Generator[Tuple[int, "np.ndarray"], None, None]:
    """
    Yield frames from a webcam or RTSP/HTTP stream.

    This is designed for live preview / WebSocket-style streaming,
    not for long-term batch processing.
    """
    import time
    import numpy as np  # noqa

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open webcam/stream: {source}")

    interval = 1.0 / max(target_fps, 0.1)
    frame_index = 0

    try:
        while True:
            started = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            yield frame_index, frame.copy()
            frame_index += 1

            elapsed = time.time() - started
            sleep_for = interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
    finally:
        cap.release()

