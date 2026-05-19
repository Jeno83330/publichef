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
            
            print("[AI ENGINE PRO] Analyse technique de la photo...")
            prompt = (
                "Tu es un critique culinaire factuel. Analyse cette photo. "
                "Liste uniquement les ingrédients clés, les textures visibles, le type de viande ou poisson, la garniture, et la sauce. "
                "Ne fais aucune phrase poétique, donne juste les faits précis."
            )
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=[types.Part.from_bytes(data=raw_bytes, mime_type="image/jpeg"), prompt]
            )
            return response.text.strip()
        except Exception as e:
            print(f"\n[AI ENGINE ERROR] : {traceback.format_exc()}")
            return "Plat de chef, ingrédients frais de saison."

    def generate_facebook_caption(self, description):
        try:
            print("[AI ENGINE PRO] Rédaction du post Facebook gourmand...")
            prompt = (
                f"Tu es un chef cuisinier étoilé et un expert en marketing gastronomique. "
                f"Rédige un post Facebook de 3 à 4 lignes basé EXACTEMENT sur ces éléments du plat : '{description}'.\n"
                f"CONSIGNES STRICTES :\n"
                f"- Ton direct, gourmand, passionné, qui donne immédiatement faim.\n"
                f"- Ne fais PAS de template générique (évite 'Voici le cœur de notre maison...'). Parle de CE PLAT précis.\n"
                f"- 2 ou 3 émojis maximum.\n"
                f"- AUCUN numéro de téléphone, AUCUNE fausse adresse.\n"
                f"- Termine par une courte phrase invitant à venir le déguster."
            )
            response = self.client.models.generate_content(model='gemini-2.5-pro', contents=prompt)
            return response.text.strip()
        except Exception as e:
            return "Notre plat signature vous attend aujourd'hui. Venez découvrir l'explosion de saveurs imaginée par notre chef."

    def generate_hashtags(self, description):
        try:
            prompt = f"Génère une seule ligne contenant 5 ou 6 hashtags culinaires impactants liés à ces éléments : '{description}'. Sépare-les par des espaces."
            response = self.client.models.generate_content(model='gemini-2.5-pro', contents=prompt)
            return response.text.strip()
        except Exception as e:
            return "#Restaurant #FaitMaison #Gastronomie #Chef #Gourmandise"
