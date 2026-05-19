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
            # 🧹 CORRECTIF : On nettoie l'étiquette Safari "data:image/jpeg;base64,"
            if "," in b64_data:
                b64_data = b64_data.split(",")[1]
                
            raw_bytes = base64.b64decode(b64_data)
            print("[AI ENGINE PRO] Analyse de la texture et des cuissons...")
            
            prompt = (
                "Tu es un chef cuisinier étoilé et un expert en marketing gastronomique. "
                "Analyse cette photo de plat de restaurant de manière approfondie. Repère les ingrédients clés, "
                "les textures (croustillant, fondant, caramélisé), la cuisson et la présentation. "
                "Rédige une synthèse courte mais extrêmement gourmande qui met en valeur le savoir-faire artisanal du plat."
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
            print(f"\n[AI ENGINE ERROR DESCRIBE] : {traceback.format_exc()}")
            return "Un magnifique plat signature préparé avec passion par notre chef."

    def generate_facebook_caption(self, description):
        try:
            prompt = f"En t'appuyant sur cette analyse de plat : '{description}', rédige une légende publicitaire d'élite pour le compte Facebook d'un restaurant de qualité.\n\n" \
                     f"CONSIGNES STRICTES :\n" \
                     f"- Rédige un texte captivant et chaleureux de 3 à 4 phrases maximum.\n" \
                     f"- Adopte le ton d'un restaurateur passionné.\n" \
                     f"- Utilise un vocabulaire riche et évocateur qui donne immédiatement faim.\n" \
                     f"- Intègre des émojis élégants.\n" \
                     f"- NE parle JAMAIS de prix, de réservations, de lien ou de numéro de téléphone.\n" \
                     f"- Va droit au but."
            
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"\n[AI ENGINE ERROR CAPTION] : {traceback.format_exc()}")
            return "Une suggestion exclusive à découvrir aujourd'hui ! Notre équipe a hâte de vous faire partager cette explosion de saveurs artisanales."

    def generate_hashtags(self, description):
        try:
            prompt = f"Génère une seule ligne contenant exactement entre 6 et 8 hashtags culinaires ciblés, haut de gamme et séparés par des espaces, basés sur cette description : '{description}'."
            
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return "#restaurant #gastronomie #faitmaison #chef"
