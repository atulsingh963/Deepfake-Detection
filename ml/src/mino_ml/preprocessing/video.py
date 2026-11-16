import os
import subprocess
import json
import tempfile
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

class VideoPreprocessor:
    def __init__(self, sample_frames: int = 16):
        self.sample_frames = sample_frames

    def inspect_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Runs ffprobe safely with array arguments.
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(res.stdout)
            video_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
            
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))
            duration = float(info.get("format", {}).get("duration", 0.0))
            codec = video_stream.get("codec_name", "unknown")
            
            return {
                "width": width,
                "height": height,
                "duration_seconds": duration,
                "codec": codec,
            }
        except Exception as e:
            # Fallback to OpenCV if ffprobe encounters container error
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Unable to read video stream: {e}")
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            dur = total_frames / fps if fps > 0 else 0.0
            cap.release()
            return {
                "width": w,
                "height": h,
                "duration_seconds": dur,
                "codec": "opencv_fallback"
            }

    def sample_video_frames(self, video_path: str, count: int = 16) -> List[Tuple[int, int, np.ndarray]]:
        """
        Samples evenly spaced frames from video.
        Returns list of tuples: (frame_index, timestamp_ms, frame_bgr)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Failed to open video file for frame extraction")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

        if total_frames <= 0:
            cap.release()
            return []

        indices = np.linspace(0, total_frames - 1, min(count, total_frames), dtype=int)
        sampled = []

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret and frame is not None:
                timestamp_ms = int((idx / fps) * 1000)
                sampled.append((int(idx), timestamp_ms, frame))

        cap.release()
        return sampled

video_preprocessor = VideoPreprocessor()
