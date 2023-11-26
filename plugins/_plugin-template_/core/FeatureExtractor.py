import numpy as np
import onnxruntime as ort
from PIL import Image


class FeatureExtractor:
    """Модуль по поиску фичей через отклик ResNet18"""

    def __init__(self, config: dict) -> None:
        self.input_shape = config["input_shape"]
        self.weights = config["weights"]
        self.normalize_mean = config["normalize_mean"]
        self.normalize_std = config["normalize_std"]
        self.model = ort.InferenceSession("ResNET_based_detector/models/resnet18.onnx")

    def extract_feature_vector(self, frame):
        input_tensor = self.preprocess_frame(frame)
        outputs = self.model.run(["output"], {"images": input_tensor})
        # << PASTE/CUSTOMIZE YOUR CODE HERE >>
        return outputs[0].flatten()

    def preprocess_frame(self, frame):
        # << PASTE/CUSTOMIZE YOUR CODE HERE >>

        frame = frame.convert("RGB")
        width, height = frame.size
        if width < height:
            height = int(height * self.input_shape / width)
            width = self.input_shape
        else:
            width = int(width * self.input_shape / height)
            height = self.input_shape
        frame = frame.resize((width, height), resample=Image.Resampling.BILINEAR)
        frame = np.asarray(frame).astype("float32")
        frame = (frame / 255 - self.normalize_mean) / self.normalize_std
        return frame.transpose(2, 0, 1).astype(np.float32)[np.newaxis, ...]
