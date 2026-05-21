import os
import base64
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

class AIEngine:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = 'gemini-2.5-flash'
        
        self.system_instruction = (
            "Tu es le community manager de L'Athelia Resto, situé dans la zone Athelia à La Ciotat. "
            "Ton style est authentique, direct et chaleureux, parfait pour les travailleurs du coin à la pause déjeuner. "
            "Règle absolue : n'utilise JAMAIS de clichés ridicules comme 'explosion de saveurs', 'régal pour les papilles' ou 'voyage culinaire'. "
            "Parle de cuisine maison, de bons produits bruts et de la convivialité du lieu."
        )

    def _compress_image(self, image_bytes):
        """Redimensionne et compresse l'image pour réduire drastiquement les coûts de l'API"""
        img = Image.open(BytesIO(image_bytes))
        
        # Convertir en RGB si nécessaire (pour le format JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Redimensionner si l'image est immense (max 1024px de large ou de haut)
        img.thumbnail((1024, 1024))
        
        # Sauvegarder avec une compression de 75%
        output = BytesIO()
        img.save(output, format="JPEG", quality=75)
        return output.getvalue()

    def describe_dish_from_bytes(self, image_b64):
        raw_bytes = base64.b64decode(image_b64)
        
        # Application de la compression économique
        compressed_bytes = self._compress_image(raw_bytes)
        
        prompt = "Analyse cette assiette avec l'œil d'un cuisinier. Quels sont les ingrédients, les textures et les cuissons visibles ?"
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=compressed_bytes, mime_type='image/jpeg'),
                prompt
            ],
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7
            )
        )
        return response.text

    def generate_facebook_caption(self, description):
        prompt = f"Rédige le post de présentation de ce plat du jour à partir de ces éléments : {description}. Sois court, naturel et percutant. N'ajoute pas de numéro de téléphone ni de hashtags à la fin."
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.8
            )
        )
        return response.text

    def generate_hashtags(self, description):
        prompt = f"Génère 5 hashtags précis pour ce plat : {description}. Inclus obligatoirement #AtheliaResto et #LaCiotat. Renvoie juste les hashtags séparés par des espaces."
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )
        return response.text
