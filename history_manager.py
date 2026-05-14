"""
history_manager.py — Gestion de l'historique des posts PubliChef
"""

import json
import shutil
from pathlib import Path
from datetime import datetime


HISTORY_FILE = Path("history/posts.json")
HISTORY_IMAGES = Path("history/images")


def init_history():
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_IMAGES.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]")


def save_post(image_path: Path, description: str, instagram: str, facebook: str, hashtags: str) -> dict:
    init_history()

    # Copie l'image dans le dossier historique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_image = HISTORY_IMAGES / f"post_{timestamp}.jpg"
    shutil.copy(str(image_path), str(saved_image))

    # Crée l'entrée
    post = {
        "id": timestamp,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "image": str(saved_image),
        "description": description,
        "instagram": instagram,
        "facebook": facebook,
        "hashtags": hashtags
    }

    # Charge et met à jour l'historique
    posts = json.loads(HISTORY_FILE.read_text())
    posts.insert(0, post)
    HISTORY_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2))

    return post


def get_all_posts() -> list:
    init_history()
    return json.loads(HISTORY_FILE.read_text())


def get_post_by_id(post_id: str) -> object:
    posts = get_all_posts()
    for post in posts:
        if post["id"] == post_id:
            return post
    return None


def delete_post(post_id: str) -> bool:
    posts = get_all_posts()
    new_posts = [p for p in posts if p["id"] != post_id]
    if len(new_posts) < len(posts):
        HISTORY_FILE.write_text(json.dumps(new_posts, ensure_ascii=False, indent=2))
        return True
    return False