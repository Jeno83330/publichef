import os
from genai import Client

class AIEngine:
    def __init__(self):
        self.client = Client()
        self.model = "gemini-2.5-flash"

    def _call_modern_api(self, contents):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            return response.text
        except Exception as e:
            print(f"[ERROR AI_ENGINE 2.5] : {str(e)}")
            return "Erreur lors de la génération du texte avec le nouveau moteur."

    def describe_dish_from_bytes(self, img_b64):
        import base64
        from PIL import Image
        import io
        
        image_data = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(image_data))
        
        prompt = "Analyse cette photo de plat. Donne une description culinaire ultra-précise, gastronomique et vendeuse du plat."
        return self._call_modern_api([img, prompt])

    def generate_facebook_caption(self, description):
        prompt = f"Rédige une légende captivante pour Facebook et Instagram basée sur : '{description}'. Ton chaleureux, pro, axé cuisine maison. Invitation à réserver, pas de numéro de téléphone."
        return self._call_modern_api([prompt])

    def generate_hashtags(self, description):
        prompt = f"Génère une ligne de 8 hashtags pertinents séparés par des espaces basés sur : '{description}'. Inclus #LaCiotat."
        return self._call_modern_api([prompt])
