import os
import base64
import traceback
from google import genai
from google.genai import types

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
        self.client = genai.Client(api_key=api_key)

    def describe_dish_from_bytes(self, b64_data):
        try:
            if "," in b64_data:
                b64_data = b64_data.split(",")[1]
            raw_bytes = base64.b64decode(b64_data)
            
            print("[AI ENGINE PRO] Analyse de la photo pour une description unique...")
            
            prompt = (
                "Tu es un chef cuisinier étoilé et un expert en marketing gastronomique. "
                "Analyse cette photo de plat de restaurant de manière approfondie. "
                "Repère les ingrédients clés, les textures (croustillant, fondant, caramélisé), la cuisson et la présentation. "
                "Rédige une suggestion de présentation et de saveurs en 3-4 phrases pour Facebook, en adoptant le ton d'un restaurateur passionné. "
                "Ne fais PAS de template générique. Parle de CE PLAT spécifique. "
                "Utilise un vocabulaire riche et évocateur qui donne immédiatement faim. Ajoute 2-3 émojis pertinents."
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=[
                    types.Part.from_bytes(data=raw_bytes, mime_type="image/jpeg"),
                    prompt
                ]
            )
            return response.text.strip()
        except Exception as e:
            print(f"\n[AI ENGINE ERROR] : {traceback.format_exc()}")
            return "Une suggestion exclusive à découvrir aujourd'hui ! Notre équipe a hâte de vous faire partager cette explosion de saveurs artisanales."

    def generate_hashtags(self, description):
        try:
            prompt = f"En t'appuyant sur cette description de plat : '{description}', génère une seule ligne contenant entre 6 et 8 hashtags culinaires ciblés, haut de gamme et séparés par des espaces."
            response = self.client.models.generate_content(model='gemini-2.5-pro', contents=prompt)
            return response.text.strip()
        except Exception as e:
            return "#restaurant #gastronomie #faitmaison #chef #suggestion"
