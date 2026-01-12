# vision/clip_similarity.py
import os
import faiss
import numpy as np
import pandas as pd
from PIL import Image
from vision.clip_model import get_image_embedding, _load_model
import torch
import streamlit as st

_index = None
_image_paths = None
_metadata = None

def _load_resources():
    global _index, _image_paths, _metadata

    if _index is not None and _metadata is not None:
        return  # Ya cargado

    # Rutas de archivos
    index_path = "data/embeddings/index.faiss"
    image_paths_path = "data/embeddings/image_paths.npy"
    metadata_path = "data/metadata_clean.csv"

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"No se encontró {index_path}")
    if not os.path.exists(image_paths_path):
        raise FileNotFoundError(f"No se encontró {image_paths_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"No se encontró {metadata_path}")

    _index = faiss.read_index(index_path)
    _image_paths = np.load(image_paths_path, allow_pickle=True)
    _metadata = pd.read_csv(metadata_path)
    _metadata["id"] = _metadata["id"].astype(str).str.strip().str.lower()

def build_clip_query_generic(item: dict) -> str:
    """
    Construye un texto para CLIP usando todos los campos del diccionario.
    Cada campo se concatena como "clave: valor".
    Funciona para cualquier número de campos nuevos.
    """
    return "; ".join(f"{k}: {v}" for k, v in item.items() if k != "explanation" and v)

def search_multiple_queries(queries, k=5):
    """
    Realiza búsquedas en el índice FAISS para múltiples queries y obtiene resultados.
    Args:
        queries: lista de dicts con campos de cada sugerencia
        k: resultados a mostrar por query
    Returns:
        dict: {query_texto: [resultados]}
    """
    _load_resources()
    results = {}

    for item in queries:
        query_text = build_clip_query_generic(item)  # usar string para la clave
        embedding = get_text_embedding(item).astype("float32")
        faiss.normalize_L2(embedding)

        D, I = _index.search(embedding, k * 2)
        query_results = []

        for idx, score in zip(I[0], D[0]):
            img_path = _image_paths[idx]
            img_name = os.path.basename(img_path).strip().lower()
            row = _metadata[_metadata["id"] == img_name]
            if row.empty:
                continue

            metadata = row.iloc[0].to_dict()
            item_name = metadata.get("productDisplayName", "Desconocido")

            # Filtros de género y estación
            gender_filter = st.session_state.get("gender", "All")
            season_filter = st.session_state.get("season", "All")
            if gender_filter != "All" and metadata["gender"] != gender_filter:
                continue
            if season_filter != "All" and metadata["season"] != season_filter:
                continue

            query_results.append({
                "image_path": img_path,
                "score": float(score),
                "item_name": item_name
            })

            if len(query_results) == k:
                break

        results[query_text] = query_results

    return results


def get_text_embedding(text):
    model, processor = _load_model()
    if isinstance(text, dict):
        text = build_clip_query_generic(text)
    inputs = processor(text=text, return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        text_embedding = model.get_text_features(**inputs)
    return text_embedding.cpu().numpy()