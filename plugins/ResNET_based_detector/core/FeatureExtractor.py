import numpy as np

import torch
import torchvision.models as models
import torchvision.transforms as transforms

from typing import Callable


class FeatureExtractor:
    """Модуль по поиску фичей через отклик ResNet18"""

    def __init__(self, config: dict) -> None:
        input_shape = config["input_shape"]
        weights = config["weights"]
        self.normalize_mean = config["normalize_mean"]
        self.normalize_std = config["normalize_std"]

        self.extract_feature_vector = self.load_resnet18_feature_extractor(input_shape, weights)

    def load_resnet18_feature_extractor(
        self, input_shape: int, weights: str
    ) -> Callable[[np.ndarray], np.ndarray]:
        """Формирует функцию для поиска feature-вектора.

        Args:
            input_shape (int): размер входной картинки.

        Returns:
            Callable[[np.ndarray], np.ndarray]: функция для поиска feature-вектора
        """

        if weights == "resnet-18":
            weights = models.ResNet18_Weights.DEFAULT
        elif weights == "resnet-34":
            weights = models.ResNet34_Weights.DEFAULT
        elif weights == "resnet-50":
            weights = models.ResNet50_Weights.DEFAULT
        else:
            raise ValueError(f"Unknown weights: {weights}")

        resnet18 = models.resnet18(weights=weights)
        resnet18.eval()

        feature_extractor = torch.nn.Sequential(*list(resnet18.children())[:-1])
        transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize(input_shape),
                transforms.ToTensor(),
                transforms.Normalize(mean=self.normalize_mean, std=self.normalize_std),
            ]
        )

        feature_extractor = (
            lambda frame: resnet18(torch.unsqueeze(transform(frame), 0))
            .view(-1)
            .detach()
            .cpu()
            .numpy()
        )

        return feature_extractor
