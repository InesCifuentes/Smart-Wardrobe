# vision/clip_model.py

import torch
from transformers import CLIPProcessor, CLIPModel

device = "cuda" if torch.cuda.is_available() else "cpu"

_model = None
_processor = None

def _load_model():
    global _model, _processor
    if _model is None:
        _model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32"
        ).to(device)

        _processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32",
            use_fast=False
        )
    return _model, _processor

def get_image_embedding(image):
    model, processor = _load_model()
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    return emb.cpu().numpy()
