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

        MAX_SIZE = (1024, 1024)
        dish_img.thumbnail(MAX_SIZE, Image.LANCZOS)
        env_img.thumbnail(MAX_SIZE, Image.LANCZOS)

        prompt = (
            "You are the world's best food photographer, shooting for a 3-Michelin-star restaurant cookbook. "
            "I give you TWO images: "
            "Image 1: a dish on transparent background PNG. "
            "Image 2: a real restaurant interior as background scene. "
            "YOUR MISSION: Create a stunning, magazine-quality food photograph by perfectly compositing the dish into the scene. "
            "PERSPECTIVE & PLACEMENT (CRITICAL): "
            "- Carefully analyze the exact vanishing point, horizon line and camera angle of the background table. "
            "- The plate MUST be perfectly perspective-corrected to match the table surface angle exactly. "
            "- Place the plate directly ON the table, touching the surface naturally, never floating. "
            "- Scale: a dinner plate is 28cm diameter - scale it correctly relative to visible table elements. "
            "- Position: center-frame, slightly forward, like a hero shot. "
            "LIGHTING & SHADOWS (CRITICAL): "
            "- Identify the main light source direction in the background photo. "
            "- Add a soft, realistic shadow directly under the plate edge matching that light direction. "
            "- Add subtle ambient occlusion where plate meets table. "
            "- The food should have beautiful specular highlights making it look fresh and appetizing. "
            "COLOR GRADING (CRITICAL): "
            "- Apply professional food photography color grading: warm shadows, bright highlights. "
            "- Boost food colors: meat should look rich and brown, vegetables vivid green, sauces glossy. "
            "- Overall warmth: add a golden hour feel, like shooting near a window at sunset. "
            "- Contrast: boost by 25 percent for a magazine look. Saturation: boost food colors by 20 percent. "
            "- The final image should look like it was shot on a Hasselblad medium format camera. "
            "DEPTH OF FIELD: "
            "- The dish must be razor sharp, tack-focused. "
            "- Background blurred with beautiful smooth bokeh. "
            "- Transition from sharp to blur should be gradual and natural. "
            "QUALITY STANDARD: "
            "- Zero compositing artifacts, zero hard edges around the plate. "
            "- The result must be indistinguishable from a real photograph taken on location. "
            "- Think: this image will appear on the cover of a Michelin restaurant guide. "
            "OUTPUT: Return ONLY the final composite photograph. No text, no watermark, no border, no explanation."
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