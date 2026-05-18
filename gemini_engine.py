"""
gemini_engine.py — Version optimisée pour PubliChef (Insertion géométrique réelle)
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

    def compose_dish_in_environment(
        self,
        dish_path: Path,
        environment_path: Path,
    ) -> Path:

        output_dir = dish_path.parent.parent / "composed"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"final_{dish_path.stem}.jpg"

        # Ouverture des images avec un gestionnaire de contexte pour libérer la RAM immédiatement après
        with Image.open(dish_path) as dish_img, Image.open(environment_path) as env_img:
            if dish_img.mode != "RGBA":
                dish_img = dish_img.convert("RGBA")
            if env_img.mode != "RGB":
                env_img = env_img.convert("RGB")

            # Redimensionnement préventif à 1024x1024 max pour éviter les crashs RAM sur Render (512MB)
            MAX_SIZE = (1024, 1024)
            dish_img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
            env_img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)

            # PROMPT OPTIMISÉ : Focus absolu sur la géométrie, l'échelle et l'ancrage au sol
            compose_prompt = (
                "You are an expert digital compositor and professional food photographer. "
                "I have provided two images: 1) A main dish plate, and 2) A restaurant environment background. "
                "YOUR MISSION: Insert the dish into the environment photo with perfect geometric and physical realism. "
                
                "1. GEOMETRY & SCALE: Analyze the perspective, tilt, and orientation of the wooden table surface in the background. "
                "Resize, rotate, and skew the plate so its angle matches the table's plane perfectly. "
                "The plate must look like it is physically resting flat ON the table, not hovering or sliding. "
                
                "2. LIGHTING & BLENDING: Match the warm, golden ambient lighting of the restaurant. "
                "Synthesize realistic, soft contact shadows (ambient occlusion) directly underneath and around the base of the plate "
                "where it touches the wood. The edges of the plate must blend smoothly with the environment background textures. "
                
                "3. QUALITY & ENHANCEMENT: Enhance the crispness and rich textures of the food (glistening meat, vibrant garnishes) "
                "while maintaining a professional shallow depth of field (sharp dish, soft bokeh background). "
                "Do not change the food's identity; make it look highly appetizing. "
                
                "Return ONLY the final composited JPEG image."
            )

            # Un seul appel API au lieu de deux : gain de vitesse massif et économie de RAM
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

        # Extraction et sauvegarde de l'image finale renvoyée par Gemini
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                # Utilisation de BytesIO pour traiter l'image en RAM sans fichier PNG temporaire sur Render
                input_buffer = io.BytesIO(part.inline_data.data)
                
                with Image.open(input_buffer) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    # Sauvegarde directe au format JPEG avec une qualité optimisée pour le Web
                    img.save(output_path, "JPEG", quality=90)
                    
                return output_path

        raise Exception("Gemini did not return an image")