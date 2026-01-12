import pandas as pd
from typing import Optional


def normalize_id(image_id: str) -> str:
    """Normalize image id strings for consistent lookup."""
    if image_id is None:
        return ""
    return str(image_id).strip().lower()


def load_metadata(path: str = "data/metadata_clean.csv") -> pd.DataFrame:
    """Load metadata CSV and normalize the `id` column.

    Returns a pandas DataFrame with an `id` column normalized to lowercase
    stripped strings.
    """
    df = pd.read_csv(path)
    if "id" in df.columns:
        df["id"] = df["id"].astype(str).map(normalize_id)
    return df


def get_metadata_by_id(df: pd.DataFrame, image_id: str) -> Optional[dict]:
    """Return metadata row as dict for a given image id, or None if not found."""
    if df is None or image_id is None:
        return None
    nid = normalize_id(image_id)
    row = df[df["id"] == nid]
    if row.empty:
        return None
    return row.iloc[0].to_dict()
