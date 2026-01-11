import os
import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import pandas as pd

# ---------------- CONFIG ----------------
IMAGE_DIR = "data/images"
CSV_CLEAN = "data/metadata_clean.csv"
EMBEDDINGS_DIR = "data/embeddings"
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Dispositivo:", device)

# ---------------- CLIP ----------------
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# ---------------- METADATA ----------------
metadata = pd.read_csv(CSV_CLEAN)

available = set(os.listdir(IMAGE_DIR))
metadata = metadata[metadata["id"].isin(available)].reset_index(drop=True)

image_paths = [os.path.join(IMAGE_DIR, img) for img in metadata["id"]]

# ---------------- EMBEDDINGS ----------------
embeddings = []

total = len(image_paths)

for i, path in enumerate(image_paths):
    print(f"[{i+1}/{total}] Procesando: {path}")

    image = Image.open(path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        emb = model.get_image_features(**inputs)

    emb = emb.cpu().numpy().astype("float32")
    embeddings.append(emb)


embeddings = np.vstack(embeddings)

#NORMALIZACIÓN
faiss.normalize_L2(embeddings)

# ---------------- FAISS ----------------
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)

faiss.write_index(index, "data/embeddings/index.faiss")
np.save("data/embeddings/image_paths.npy", image_paths)

print("Índice FAISS regenerado correctamente")
