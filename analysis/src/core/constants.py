import json
import os
from functools import lru_cache
from typing import Dict, List


def load_brand_variants() -> Dict[str, List[str]]:
    """Load brand variants from brands.json. Raises error if loading fails."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "brands.json")

    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Critical error: {json_path} not found. "
            "Brand analysis cannot proceed."
        )

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


BRAND_VARIANTS: Dict[str, List[str]] = load_brand_variants()


@lru_cache(maxsize=256)
def _contains_chinese(text: str) -> bool:
    """Check if text contains Chinese characters"""
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return True
    return False


@lru_cache(maxsize=128)
def get_brand_variants(brand: str) -> List[str]:
    """Get variants for a brand, including defaults."""
    for variants in BRAND_VARIANTS.values():
        if brand in variants:
            return variants

    # Default variants generation
    variants = [brand]
    if not _contains_chinese(brand):
        variants.extend([brand.lower(), brand.upper(), brand.capitalize()])
    return list(set(variants))
