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

        enhance_prompt = (
            "You are both a Michelin 3-star chef and a world-class food photographer and retoucher. "
            "I give you a dish photo on transparent background. "
            "YOUR MISSION: Sublimate this dish while keeping it 100 percent RECOGNIZABLE. Same dish, same ingredients, same plate. "
            "STEP 1 - DRESSING IMPROVEMENT: "
            "Slightly improve the plating presentation like a professional chef would. "
            "Straighten elements, add a touch of elegance, make it look meticulously plated. "
            "Small precise adjustments only: better positioning of garnishes, cleaner sauce placement, "
            "more appetizing arrangement of ingredients. Do NOT completely change the dish. "
            "The person must recognize their dish but think WOW it looks so much better. "
            "STEP 2 - PROFESSIONAL COLOR AND TEXTURE ENHANCEMENT: "
            "Meats: rich brown caramelization, visible appetizing texture, beautiful crust. "
            "Vegetables: vivid fresh colors, crisp and bright. "
            "Sauces: glossy, shiny, professional restaurant finish. "
            "Garnishes: perfectly placed, elegant, fresh. "
            "Plate: clean edges, no smudges, pristine presentation. "
            "STEP 3 - LIGHTING AND RETOUCHING: "
            "Add warm professional food photography lighting with beautiful highlights. "
            "Boost contrast by 20 percent for a magazine look. "
            "Boost saturation by 15 percent to make food colors pop. "
            "Add subtle specular highlights to make food look fresh and appetizing. "
            "RESULT: A stunning Michelin-quality dish photo that looks professionally shot and plated. "
            "Keep the transparent background intact. Return ONLY the enhanced dish image, no text."
        )

        enhance_response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[enhance_prompt, dish_img],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                temperature=0.3
            )
        )

        for part in enhance_response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                enhanced_dish_path = output_dir / "enhanced_dish_temp.png"
                enhanced_dish_path.write_bytes(part.inline_data.data)
                dish_img = Image.open(enhanced_dish_path)
                if dish_img.mode != "RGBA":
                    dish_img = dish_img.convert("RGBA")
                break

        compose_prompt = (
            "You are the world best food photographer shooting for a 3-Michelin-star restaurant cookbook. "
            "I give you TWO images: "
            "Image 1: a professionally retouched dish on transparent background PNG. "
            "Image 2: a real restaurant interior as background scene. "
            "YOUR MISSION: Create a stunning magazine-quality food photograph by compositing the dish into the scene. "
            "PERSPECTIVE AND PLACEMENT CRITICAL: "
            "Carefully analyze the exact vanishing point, horizon line and camera angle of the background table. "
            "The plate MUST be perfectly perspective-corrected to match the table surface angle exactly. "
            "The plate MUST physically rest ON the table surface with FULL CONTACT, absolutely NO floating, NO gap between plate bottom and table. "
            "The plate bottom edge must touch and slightly compress against the table surface to look real. "
            "Scale: a dinner plate is 28cm diameter, scale it correctly relative to visible table elements. "
            "Position: center-frame, slightly forward, like a hero shot. "
            "LIGHTING AND SHADOWS CRITICAL: "
            "Identify the main light source direction in the background photo. "
            "Add a soft realistic shadow directly under the plate matching that light direction. "
            "Add subtle ambient occlusion where plate meets table surface. "
            "The food should have beautiful specular highlights. "
            "COLOR GRADING: "
            "Apply professional food photography color grading: warm shadows, bright highlights. "
            "Overall warmth: golden hour feel. "
            "Contrast boost 25 percent for magazine look. "
            "DEPTH OF FIELD: "
            "The dish must be razor sharp and tack-focused. "
            "Background blurred with beautiful smooth bokeh. "
            "QUALITY STANDARD: "
            "Zero compositing artifacts, zero hard edges around the plate. "
            "The result must be indistinguishable from a real photograph taken on location. "
            "This image will appear on the cover of a Michelin restaurant guide. "
            "OUTPUT: Return ONLY the final composite photograph. No text, no watermark, no border."
        )

        response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[compose_prompt, dish_img, env_img],
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
