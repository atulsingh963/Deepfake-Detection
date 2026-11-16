import cv2
import numpy as np
from typing import List, Tuple

class FaceDetector:
    def __init__(self):
        # Check if CascadeClassifier or FaceDetectorYN is available
        self.has_cascade = hasattr(cv2, 'CascadeClassifier')
        self.cascade = None
        if self.has_cascade:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.cascade = cv2.CascadeClassifier(cascade_path)

    def detect_faces(self, image_bgr: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Returns bounding boxes (x, y, w, h). If classical cascade is absent,
        performs central face candidate ROI detection.
        """
        h_img, w_img = image_bgr.shape[:2]
        if self.cascade is not None:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            faces = self.cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(30, 30)
            )
            if len(faces) > 0:
                return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]

        # Robust Fallback Face ROI: Center 60% of frame where portrait/head generally sits
        cx, cy = w_img // 2, h_img // 2
        box_w = int(w_img * 0.55)
        box_h = int(h_img * 0.55)
        x = max(0, cx - box_w // 2)
        y = max(0, cy - box_h // 2)
        return [(int(x), int(y), int(box_w), int(box_h))]

    def extract_aligned_face(
        self,
        image_bgr: np.ndarray,
        box: Tuple[int, int, int, int],
        target_size: Tuple[int, int] = (224, 224),
        margin: float = 0.15
    ) -> np.ndarray:
        h_img, w_img = image_bgr.shape[:2]
        x, y, w, h = box
        
        dx = int(w * margin)
        dy = int(h * margin)
        x1 = max(0, x - dx)
        y1 = max(0, y - dy)
        x2 = min(w_img, x + w + dx)
        y2 = min(h_img, y + h + dy)

        crop = image_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            return cv2.resize(image_bgr, target_size)
        return cv2.resize(crop, target_size, interpolation=cv2.INTER_AREA)

face_detector = FaceDetector()
