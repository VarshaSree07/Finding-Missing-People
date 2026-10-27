from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

import numpy as np


BBox = Tuple[float, float, float, float]  # x1, y1, x2, y2


def iou(box_a: BBox, box_b: BBox) -> float:
    """Compute IoU (intersection over union) between two boxes."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return inter_area / union


@dataclass
class Track:
    track_id: int
    bbox: BBox
    last_seen_frame: int
    hits: int = 1
    time_since_update: int = 0
    embedding: Any | None = None  # cached face embedding
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleSORT:
    """
    Minimal SORT-style tracker for face boxes.

    This is not a full DeepSORT but good enough to:
      - assign stable IDs per person across frames
      - avoid re-embedding the same person many times
    """

    def __init__(
        self,
        max_age: int = 15,
        min_hits: int = 1,
        iou_threshold: float = 0.3,
    ) -> None:
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold

        self._next_id = 1
        self.tracks: Dict[int, Track] = {}

    def _create_track(self, bbox: BBox, frame_index: int) -> Track:
        track = Track(
            track_id=self._next_id,
            bbox=bbox,
            last_seen_frame=frame_index,
        )
        self.tracks[self._next_id] = track
        self._next_id += 1
        return track

    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_index: int,
    ) -> List[Track]:
        """
        Update tracker with detections for the current frame.

        Args:
            detections: list of dicts with at least 'bbox'
            frame_index: current frame index

        Returns:
            active tracks after update.
        """
        # Age all existing tracks
        for t in self.tracks.values():
            t.time_since_update += 1

        det_bboxes: List[BBox] = [tuple(d["bbox"]) for d in detections]

        if det_bboxes:
            # Build IoU matrix (tracks x detections)
            track_ids = list(self.tracks.keys())
            iou_matrix = np.zeros((len(track_ids), len(det_bboxes)), dtype=float)

            for ti, tid in enumerate(track_ids):
                tb = self.tracks[tid].bbox
                for di, db in enumerate(det_bboxes):
                    iou_matrix[ti, di] = iou(tb, db)

            # Greedy assignment: repeatedly pick best IoU above threshold
            assigned_dets = set()
            assigned_tracks = set()

            while True:
                ti, di = divmod(int(np.argmax(iou_matrix)), iou_matrix.shape[1])
                if iou_matrix[ti, di] < self.iou_threshold:
                    break
                if ti in assigned_tracks or di in assigned_dets:
                    iou_matrix[ti, di] = -1
                    continue

                track_id = track_ids[ti]
                track = self.tracks[track_id]
                track.bbox = det_bboxes[di]
                track.last_seen_frame = frame_index
                track.time_since_update = 0
                track.hits += 1

                # Attach detection metadata (e.g. confidence) to track
                track.metadata.update({k: v for k, v in detections[di].items() if k != "bbox"})

                assigned_tracks.add(ti)
                assigned_dets.add(di)
                iou_matrix[ti, :] = -1
                iou_matrix[:, di] = -1

            # Create new tracks for unassigned detections
            for di, db in enumerate(det_bboxes):
                if di not in assigned_dets:
                    det = detections[di]
                    track = self._create_track(db, frame_index)
                    track.metadata.update({k: v for k, v in det.items() if k != "bbox"})

        # Drop stale tracks
        to_delete = [
            tid
            for tid, t in self.tracks.items()
            if t.time_since_update > self.max_age
        ]
        for tid in to_delete:
            del self.tracks[tid]

        # Return active tracks (only those with enough hits if min_hits > 1)
        active_tracks = [
            t
            for t in self.tracks.values()
            if t.hits >= self.min_hits
        ]
        return active_tracks

