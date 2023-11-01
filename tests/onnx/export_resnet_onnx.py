# Экспорт ResNet в ONNX с поддержкой батчей и произвольного размера изображений

import torch
import torchvision.models as models

resnet18 = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

dummy_input = torch.randn(1, 3, 224, 224)
input_names = ["images"]
output_names = ["output"]

dynamic_axes_dict = {
    'images': {
        0: 'batch_size',
        2: 'height',
        3: 'width'
    },
    'output': {
        0: 'batch_size'
    }
}

torch.onnx.export(
    resnet18,
    dummy_input,
    "resnet18.onnx",
    verbose=False,
    input_names=input_names,
    output_names=output_names,
    dynamic_axes=dynamic_axes_dict,
    export_params=True,
)
