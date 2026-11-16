import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional

class Detector(ABC):
    @abstractmethod
    def load(self, checkpoint_path: Optional[str] = None):
        pass

    @abstractmethod
    def predict_face_crop(self, face_bgr: np.ndarray) -> float:
        """Returns manipulation probability score between 0.0 and 1.0"""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        pass

class EfficientNetBaselineDetector(Detector):
    def __init__(self, device: str = "cpu"):
        self.device = torch.device(device)
        self.model: Optional[nn.Module] = None
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def load(self, checkpoint_path: Optional[str] = None):
        # Initialize EfficientNet backbone with binary classification head
        model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features, 2)
        )

        if checkpoint_path and os.path.exists(checkpoint_path):
            state_dict = torch.load(checkpoint_path, map_location=self.device)
            model.load_state_dict(state_dict)

        model.to(self.device)
        model.eval()
        self.model = model

    def predict_face_crop(self, face_bgr: np.ndarray) -> float:
        if self.model is None:
            self.load()

        # Convert BGR to RGB
        face_rgb = cv2_to_rgb(face_bgr)
        tensor = self.transform(face_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)
            # Class 1 is manipulated (deepfake)
            manipulation_score = float(probs[0, 1].item())

        return manipulation_score

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "mino-efficientnet-b0",
            "version": "v1.0.0",
            "architecture": "EfficientNet-B0 Binary Face Classifier",
            "device": str(self.device),
            "input_resolution": (224, 224)
        }

def cv2_to_rgb(img_bgr: np.ndarray) -> np.ndarray:
    import cv2
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

detector_engine = EfficientNetBaselineDetector()
