"""
decor_manager.py — Gestion des décors sauvegardés
"""

import json
import shutil
import base64
from pathlib import Path

DECORS_FILE = Path("decors/saved_decors.json")
DECORS_IMAGES = Path("decors/images")


def init_decors():
    DECORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DECORS_IMAGES.mkdir(parents=True, exist_ok=True)
    if not DECORS_FILE.exists():
        DECORS_FILE.write_text("{}")


def save_decor(decor_name: str, image_path: Path):
    init_decors()
    saved_path = DECORS_IMAGES / f"{decor_name}.jpg"
    shutil.copy(str(image_path), str(saved_path))
    decors = json.loads(DECORS_FILE.read_text())
    decors[decor_name] = str(saved_path)
    DECORS_FILE.write_text(json.dumps(decors, ensure_ascii=False))


def get_decor(decor_name: str):
    init_decors()
    decors = json.loads(DECORS_FILE.read_text())
    if decor_name in decors:
        p = Path(decors[decor_name])
        if p.exists():
            return p
    return None


def get_all_decors_b64():
    init_decors()
    decors = json.loads(DECORS_FILE.read_text())
    result = {}
    for name, path in decors.items():
        p = Path(path)
        if p.exists():
            with open(p, "rb") as f:
                result[name] = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    return result


def delete_decor(decor_name: str):
    init_decors()
    decors = json.loads(DECORS_FILE.read_text())
    if decor_name in decors:
        p = Path(decors[decor_name])
        if p.exists():
            p.unlink()
        del decors[decor_name]
        DECORS_FILE.write_text(json.dumps(decors, ensure_ascii=False))