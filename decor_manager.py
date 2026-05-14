"""
decor_manager.py — Gestion des décors sauvegardés via ImgBB
"""

import json
import base64
import requests
import os
from pathlib import Path

DECORS_FILE = Path("decors/saved_decors.json")


def init_decors():
    DECORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DECORS_FILE.exists():
        DECORS_FILE.write_text("{}")


def save_decor(decor_name: str, image_path: Path):
    init_decors()
    api_key = os.getenv("IMGBB_API_KEY")
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    if api_key:
        try:
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                data={"key": api_key, "image": img_b64, "name": f"decor_{decor_name}"}
            )
            data = response.json()
            if data.get("success"):
                url = data["data"]["url"]
                decors = json.loads(DECORS_FILE.read_text())
                decors[decor_name] = {"type": "url", "value": url}
                DECORS_FILE.write_text(json.dumps(decors, ensure_ascii=False))
                return
        except Exception:
            pass
    decors = json.loads(DECORS_FILE.read_text())
    decors[decor_name] = {"type": "base64", "value": f"data:image/jpeg;base64,{img_b64}"}
    DECORS_FILE.write_text(json.dumps(decors, ensure_ascii=False))


def get_decor_path(decor_name: str):
    init_decors()
    decors = json.loads(DECORS_FILE.read_text())
    if decor_name not in decors:
        return None
    entry = decors[decor_name]
    if entry["type"] == "url":
        import tempfile
        response = requests.get(entry["value"])
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(response.content)
        tmp.close()
        return Path(tmp.name)
    else:
        import tempfile
        img_data = base64.b64decode(entry["value"].split(",")[1])
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(img_data)
        tmp.close()
        return Path(tmp.name)


def get_all_decors_b64():
    init_decors()
    decors = json.loads(DECORS_FILE.read_text())
    result = {}
    for name, entry in decors.items():
        if entry["type"] == "url":
            result[name] = entry["value"]
        else:
            result[name] = entry["value"]
    return result


def delete_decor(decor_name: str):
    init_decors()
    decors = json.loads(DECORS_FILE.read_text())
    if decor_name in decors:
        del decors[decor_name]
        DECORS_FILE.write_text(json.dumps(decors, ensure_ascii=False))