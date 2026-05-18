import os
import base64
import traceback
import google.generativeai as genai

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
        if not api_key:
            print("[AI ENGINE] CRITICAL: Aucune clé API trouvée dans l'environnement Render !")
        
        genai.configure(api_key=api_key)
        # Utilisation de la version Flash : 100% accessible, aucune erreur 404 possible
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def describe_dish_from_bytes(self, b64_data):
        try:
            raw_bytes = base64.b64decode(b64_data)
            response = self.model.generate_content([
                {"mime_type": "image/jpeg", "data": raw_bytes},
                "Tu es un chef cuisinier étoilé et un expert en marketing gastronomique. Analyse cette photo de plat de restaurant de manière approfondie. Repère les ingrédients clés, les textures (croustillant, fondant, caramélisé), la cuisson et la présentation. Rédige une synthèse courte mais extrêmement gourmande qui met en valeur le savoir-faire artisanal du plat."
            ])
            return response.text.strip()
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
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"\n[AI ENGINE ERROR CAPTION] :\n{traceback.format_exc()}\n")
            return "Une suggestion exclusive à découvrir aujourd'hui ! Notre équipe a hâte de vous faire partager cette explosion de saveurs artisanales. Réservez votre table ! ✨"

    def generate_hashtags(self, description):
        try:
            prompt = f"Génère une seule ligne contenant exactement entre 6 et 8 hashtags culinaires ciblés, haut de gamme et séparés par des espaces, basés sur cette description : '{description}'. Exemple : #restaurateur #faitmaison #gastronomie."
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"\n[AI ENGINE ERROR HASHTAGS] :\n{traceback.format_exc()}\n")
            return #restaurant #gastronomie #faitmaison #foodporn #chef
