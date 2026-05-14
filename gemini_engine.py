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

        pprompt = (
            "You are an award-winning professional food photographer for Michelin-starred restaurants. "
            "I give you two images: "
            "1. A restaurant dish on transparent background PNG "
            "2. A restaurant interior decor as background. "
            "Create a stunning professional food photo with these strict rules: "
            "COMPOSITION: Place the dish realistically ON the table surface in the decor, properly scaled (the plate should look natural size on the table, not too big or too small). "
            "The dish must be centered and slightly in the foreground, viewed from a 45-degree angle (standard food photography angle). "
            "LIGHTING: Add warm golden restaurant lighting. Create realistic shadows under the plate. "
            "The light source should come from the upper left, creating depth and dimension. "
            "COLORS: Enhance food colors to look vibrant, fresh and appetizing. "
            "Boost saturation slightly. Make sauces glossy, vegetables vivid green, meats rich brown. "
            "Apply a warm color grade (slightly warm shadows, bright highlights). "
            "DEPTH OF FIELD: Strong bokeh effect on background, the dish must be razor sharp in focus. "
            "REALISM: The plate integration must look 100 percent photorealistic, not composited. "
            "Match the perspective and lighting of the background scene exactly. "
            "OUTPUT: Generate only the final composed image, no text, no watermark."
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