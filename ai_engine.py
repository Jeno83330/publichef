import os
import base64
import traceback
from io import BytesIO
from PIL import Image
from google import genai
from google.genai.errors import APIError

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
        self.client = genai.Client(api_key=api_key)

    def _call_with_fallback(self, contents, prompt_text=None):
        """Tente d'appeler le modèle Pro, bascule sur Flash si le Pro est surchargé (503)."""
        # Configuration des prompts selon le type de contenu
        if prompt_text and isinstance(contents, list):
            # Cas de la description d'image
            payload = [contents[0], prompt_text]
        else:
            # Cas du texte pur
            payload = contents

        # Tentative 1 : Gemini Pro
        try:
            print("[AI ENGINE] Tentative avec gemini-2.5-pro...")
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=payload
            )
            return response.text.strip()
        except APIError as e:
            if e.code == 503:
                print("[AI ENGINE WARNING] Gemini Pro est surchargé (503). Bascule immédiate sur Gemini Flash...")
                # Tentative 2 : Repli sur Gemini Flash (Ultra-disponible)
                try:
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=payload
                    )
                    return response.text.strip()
                except Exception as flash_err:
                    print(f"[AI ENGINE CRITICAL] Échec même sur le modèle Flash : {str(flash_err)}")
                    raise flash_err
            else:
                raise e

    def describe_dish_from_bytes(self, b64_data):
        try:
            raw_bytes = base64.b64decode(b64_data)
            img = Image.open(BytesIO(raw_bytes))
            
            prompt = "Tu es un chef cuisinier étoilé et un expert en marketing gastronomique. Analyse cette photo de plat de restaurant de manière approfondie. Repère les ingrédients clés, les textures (croustillant, fondant, caramélisé), la cuisson et la présentation. Rédige une synthèse courte mais extrêmement gourmande qui met en valeur le savoir-faire artisanal du plat."
            
            return self._call_with_fallback([img], prompt)
        except Exception as e:
            print(f"\n[AI ENGINE ERROR DESCRIBE] :\n{traceback.format_exc()}\n")
            return "Un magnifique plat signature préparé avec passion par notre chef."

    def generate_facebook_caption(self, description):
        try:
            prompt = f"En t'appuyant sur cette analyse de plat : '{description}', rédige une légende publicitaire d'élite pour le compte Facebook d'un restaurant de qualité.\n\n" \
                     f"CONSIGNES STRICTES :\n" \
                     f"- Rédige un texte captivant et chaleureux de 3 à 4 phrases maximum.\n" \
                     f"- Adopte le ton d'un restaurateur passionné, fier de ses produits frais et du fait maison.\n" \
                     f"- Utilise un vocabulaire riche et évocateur qui donne immédiatement faim (ex: 'juste saisi', 'explosion de saveurs', 'gourmandise absolue').\n" \
                     f"- Intègre des émojis élégants et bien placés pour aérer le texte.\n" \
                     f"- NE parle JAMAIS de prix, de réservations, de lien ou de numéro de téléphone dans ton texte.\n" \
                     f"- Va droit au but, élimine les formules robotiques comme 'Bienvenue chez nous'."
            
            return self._call_with_fallback(prompt)
        except Exception as e:
            print(f"\n[AI ENGINE ERROR CAPTION] :\n{traceback.format_exc()}\n")
            return "Une suggestion exclusive à découvrir aujourd'hui ! Notre équipe a hâte de vous faire partager cette explosion de saveurs artisanales. Réservez votre table ! ✨"

    def generate_hashtags(self, description):
        try:
            prompt = f"Génère une seule ligne contenant exactement entre 6 et 8 hashtags culinaires ciblés, haut de gamme et séparés par des espaces, basés sur cette description : '{description}'. Exemple : #restaurateur #faitmaison #gastronomie."
            
            return self._call_with_fallback(prompt)
        except Exception as e:
            print(f"\n[AI ENGINE ERROR HASHTAGS] :\n{traceback.format_exc()}\n")
            return "#restaurant #gastronomie #faitmaison #foodporn #chef"
