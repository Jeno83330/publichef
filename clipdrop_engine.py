"""
clipdrop_engine.py — Détourage automatique du plat
"""

import os
import requests
from pathlib import Path


class ClipdropEngine:

    API_URL = "https://clipdrop-api.co/remove-background/v1"

    def __init__(self):
        self.api_key = os.getenv("CLIPDROP_API_KEY")
        if not self.api_key:
            raise EnvironmentError("CLIPDROP_API_KEY manquante dans .env")

    def remove_background(self, image_path: Path) -> Path:
        """Supprime le fond de l'image et retourne le chemin PNG avec transparence."""

        output_dir = image_path.parent.parent / "detoured"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"detoured_{image_path.stem}.png"

        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        response = requests.post(
            self.API_URL,
            headers={"x-api-key": self.api_key},
            files={"image_file": ("image.jpg", image_data, "image/jpeg")},
            timeout=60,
        )

        if not response.ok:
            raise Exception(f"Clipdrop error {response.status_code}: {response.text}")

        output_path.write_bytes(response.content)
        return output_path