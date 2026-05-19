import os
import base64
import traceback
from io import BytesIO
from PIL import Image
from google import genai

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
        # Initialisation du client officiel moderne
        self.client = genai.Client(api_key=api_key)

    def describe_dish_from_bytes(self, b64_data):
        try:
            raw_bytes = base64.b64decode(b64_data)
            img = Image.open(BytesIO(raw_bytes))
            
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[
                    img,
                    "Tu es un chef cuisinier étoilé. Analyse cette photo de plat de restaurant. Repère les ingrédients principaux, les textures et la présentation pour en faire une description ultra-gourmande."
                ]
            )
            return response.text.strip()
        except Exception as e:
            print(f"[AI ENGINE ERROR] Description échouée : {str(e)}")
            return "Un magnifique plat signature préparé avec passion par notre chef."

    def generate_facebook_caption(self, description):
        try:
            prompt = f"En t'appuyant sur cette analyse : '{description}', rédige une légende Facebook d'élite de 3-4 phrases maximum. Donne faim, utilise des émojis, adopte le ton d'un restaurateur passionné. NE parle JAMAIS de prix ou de réservation."
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"[AI ENGINE ERROR] Légende échouée : {str(e)}")
            return "Une suggestion exclusive à découvrir aujourd'hui dans notre établissement ! Une explosion de saveurs artisanales à ne pas manquer. ✨"

    def generate_hashtags(self, description):
        try:
            prompt = f"Génère une seule ligne de 6 à 8 hashtags culinaires pro basés sur : '{description}'."
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return "#restaurant #gastronomie #faitmaison #chef #food"
