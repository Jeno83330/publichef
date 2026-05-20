import os
import base64
from google import genai

class AIEngine:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        # Passage au moteur PRO pour l'analyse fine et l'écriture de qualité
        self.model_name = 'gemini-1.5-pro'
        
        # Direction Artistique personnalisée 
        self.system_instruction = (
            "Tu es le community manager de L'Athelia Resto, situé dans la zone Athelia à La Ciotat. "
            "Ton style est authentique, direct et chaleureux, parfait pour les travailleurs du coin à la pause déjeuner. "
            "Règle absolue : n'utilise JAMAIS de clichés ridicules comme 'explosion de saveurs', 'régal pour les papilles' ou 'voyage culinaire'. "
            "Parle de cuisine maison, de bons produits bruts et de la convivialité du lieu."
        )

    def describe_dish_from_bytes(self, image_b64):
        image_bytes = base64.b64decode(image_b64)
        prompt = "Analyse cette assiette avec l'œil d'un cuisinier. Quels sont les ingrédients, les textures et les cuissons visibles ?"
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                {'mime_type': 'image/jpeg', 'data': image_bytes},
                prompt
            ],
            config={'system_instruction': self.system_instruction, 'temperature': 0.7}
        )
        return response.text

    def generate_facebook_caption(self, description):
        prompt = f"Rédige le post de présentation de ce plat du jour à partir de ces éléments : {description}. Sois court, naturel et percutant. N'ajoute pas de numéro de téléphone ni de hashtags à la fin."
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={'system_instruction': self.system_instruction, 'temperature': 0.8}
        )
        return response.text

    def generate_hashtags(self, description):
        prompt = f"Génère 5 hashtags précis pour ce plat : {description}. Inclus obligatoirement #AtheliaResto et #LaCiotat. Renvoie juste les hashtags séparés par des espaces."
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={'temperature': 0.2}
        )
        return response.text
