import os
import base64
import traceback
import google.generativeai as genai

class AIEngine:
    def __init__(self):
        # Scan de toutes les variables possibles pour trouver la clé Google sur Render
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
        if not api_key:
            print("[AI ENGINE] CRITICAL: Aucune clé API trouvée dans l'environnement Render !")
        
        genai.configure(api_key=api_key)
        # UPGRADE : Passage sur le modèle PRO (plume littéraire et marketing supérieure)
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def describe_dish_from_bytes(self, b64_data):
        try:
            raw_bytes = base64.b64decode(b64_data)
            response = self.model.generate_content([
                {"mime_type": "image/jpeg", "data": raw_bytes},
                "Analyse cette photo de plat de restaurant. Décris brièvement ce que c'est, ses ingrédients visibles et son aspect culinaire (gourmand, croustillant, frais, coloré) pour un menu."
            ])
            return response.text.strip()
        except Exception as e:
            print(f"\n[AI ENGINE ERROR DESCRIBE] :\n{traceback.format_exc()}\n")
            return "Un magnifique plat signature préparé avec passion par notre chef."

    def generate_facebook_caption(self, description):
        try:
            prompt = f"En t'appuyant sur cette description de plat : '{description}', rédige une légende de 3-4 phrases captivante, très chaleureuse et vendeuse pour les réseaux sociaux d'un restaurant. Donne faim, utilise des émojis pertinents et adopte un ton convivial de restaurateur passionné. Ne parle jamais de réservations ou de numéro de téléphone."
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"\n[AI ENGINE ERROR CAPTION] :\n{traceback.format_exc()}\n")
            # Changement du texte de secours pour repérer si l'erreur persiste
            return "Une suggestion exclusive à découvrir aujourd'hui ! Notre équipe a hâte de vous faire partager cette explosion de saveurs artisanales. Réservez votre table ! ✨"

    def generate_hashtags(self, description):
        try:
            prompt = f"Génère une seule ligne contenant entre 5 et 8 hashtags culinaires ciblés et séparés par des espaces, basés sur cette description : '{description}'."
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"\n[AI ENGINE ERROR HASHTAGS] :\n{traceback.format_exc()}\n")
            return "#restaurant #gastronomie #faitmaison #foodporn #chef"
