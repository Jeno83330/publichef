"""
gemini_engine.py
"""

import os
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

    def compose_dish_in_environment(
        self,
        dish_path: Path,
        environment_path: Path,
    ) -> Path:

        output_dir = dish_path.parent.parent / "composed"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"final_{dish_path.stem}.jpg"

        dish_img = Image.open(dish_path)
        env_img = Image.open(environment_path)

        if dish_img.mode != "RGBA":
            dish_img = dish_img.convert("RGBA")
        if env_img.mode != "RGB":
            env_img = env_img.convert("RGB")

        prompt = (
            "You are a world-class food photographer shooting for a Michelin restaurant magazine. "
            "I give you TWO images: "
            "Image 1: a dish on transparent background. "
            "Image 2: a restaurant table scene as background. "
            "YOUR MISSION: Composite the dish plate INTO the background scene so it looks like a real photograph taken on set. "
            "CRITICAL PERSPECTIVE RULES: "
            "- Analyze the exact camera angle and perspective of the background table. "
            "- The plate MUST match this exact same perspective and viewing angle. "
            "- If the table is seen from a 30-45 degree angle, the plate must also appear from that same 30-45 degree angle. "
            "- The plate must sit FLAT ON the table surface, not floating, not tilted incorrectly. "
            "- Scale the plate to be realistic: a dinner plate is roughly 28cm, scale it proportionally to the table size visible. "
            "CRITICAL LIGHTING RULES: "
            "- Match the exact light direction of the background scene. "
            "- Add a realistic drop shadow under the plate matching the light source. "
            "- Enhance food colors: make them vivid, warm, appetizing. Boost contrast and saturation by 20 percent. "
            "- Apply warm color grading: golden highlights, rich shadows. "
            "CRITICAL QUALITY RULES: "
            "- The plate integration must be PHOTOREALISTIC, zero compositing artifacts. "
            "- Sharp focus on the food, background slightly blurred (bokeh). "
            "- Final image must look like it was shot by a professional photographer on location. "
            "OUTPUT: Return ONLY the final composite image. No text, no watermark, no border."
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, dish_img, env_img],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                temperature=0.4
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                png_path = output_path.with_suffix(".png")
                png_path.write_bytes(part.inline_data.data)
                with Image.open(png_path) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(output_path, "JPEG", quality=95)
                return output_path

        raise Exception("Gemini did not return an image")