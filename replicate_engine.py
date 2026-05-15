"""
replicate_engine.py — Composition via Flux Pro (Replicate)
"""

import os
import requests
import replicate
import tempfile
import base64
from pathlib import Path
from PIL import Image
import io


class ReplicateEngine:

    def __init__(self):
        api_key = os.getenv("REPLICATE_API_KEY")
        if not api_key:
            raise EnvironmentError("REPLICATE_API_KEY missing from .env")
        os.environ["REPLICATE_API_TOKEN"] = api_key

    def enhance_and_compose(
        self,
        dish_path: Path,
        environment_path: Path,
        output_path: Path,
    ) -> Path:

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dish_path, "rb") as f:
            dish_b64 = base64.b64encode(f.read()).decode()

        with open(environment_path, "rb") as f:
            env_b64 = base64.b64encode(f.read()).decode()

        prompt = (
            "Professional food photography, Michelin restaurant style. "
            "A beautifully plated dish sitting directly ON the restaurant table surface. "
            "The plate physically rests on the table with full contact, no floating. "
            "Perfect perspective matching the table angle. "
            "Warm golden restaurant lighting, soft shadows under the plate. "
            "Vivid appetizing food colors, glossy sauces, crisp garnishes. "
            "Sharp focus on food, beautiful bokeh background. "
            "Magazine quality, 3-star Michelin cookbook cover photo. "
            "Photorealistic, professional food photographer style."
        )

        output = replicate.run(
            "black-forest-labs/flux-1.1-pro",
            input={
                "prompt": prompt,
                "aspect_ratio": "4:5",
                "output_format": "jpg",
                "output_quality": 95,
                "safety_tolerance": 5,
                "prompt_upsampling": True
            }
        )

        if output:
            img_url = str(output)
            response = requests.get(img_url)
            with open(str(output_path), "wb") as f:
                f.write(response.content)
            return output_path

        raise Exception("Replicate did not return an image")
