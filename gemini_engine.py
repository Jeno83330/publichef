"""
gemini_engine.py — PubliChef V2
"""

import os
import io
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types


class GeminiEngine:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY missing from .env")
        self.client = genai.Client(api_key=api_key)

    def compose_dish_in_environment(self, dish_path: Path, environment_path: Path) -> Path:

        output_dir = dish_path.parent.parent / "composed"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"final_{dish_path.stem}.jpg"

        dish_img = Image.open(dish_path)
        env_img = Image.open(environment_path)

        if dish_img.mode != "RGBA":
            dish_img = dish_img.convert("RGBA")
        if env_img.mode != "RGB":
            env_img = env_img.convert("RGB")

        MAX_SIZE = (900, 900)
        dish_img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
        env_img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)

        compose_prompt = (
            "You are an expert digital compositor and professional food photographer. "
            "I have provided two images: 1) A main dish plate, and 2) A restaurant environment background. "
            "YOUR MISSION: Insert the dish into the environment photo with perfect geometric and physical realism. "
            "1. GEOMETRY: Analyze the perspective and orientation of the table. "
            "The plate MUST rest flat ON the table. NO floating, NO gap. "
            "Scale the plate correctly relative to the table size. "
            "2. LIGHTING: Match the restaurant lighting. Add soft shadow under the plate. "
            "3. FOOD QUALITY: Enhance food colors. Sharp dish, soft bokeh background. "
            "Return ONLY the final composited JPEG image. No text, no watermark."
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[compose_prompt, dish_img, env_img],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    temperature=0.4
                )
            )
            print("[GEMINI] Modele: gemini-3-pro-image-preview")
        except Exception as e:
            if any(x in str(e) for x in ["503", "UNAVAILABLE", "high demand", "overloaded"]):
                print("[GEMINI] Fallback sur gemini-2.5-flash-image")
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[compose_prompt, dish_img, env_img],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"],
                        temperature=0.4
                    )
                )
            else:
                raise

        del dish_img
        del env_img

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                input_buffer = io.BytesIO(part.inline_data.data)
                with Image.open(input_buffer) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(output_path, "JPEG", quality=88)
                return output_path

        raise Exception("Gemini did not return an image")
