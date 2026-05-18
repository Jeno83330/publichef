import os
import base64
import google.generativeai as genai

class AIEngine:
    def __init__(self):
        # On récupère la clé Google déjà existante et configurée sur Render
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Clé API Gemini (GEMINI_API_KEY ou GOOGLE_API_KEY) introuvable dans les variables d'environnement.")
        
        genai.configure(api_key=api_key)
        # On utilise le modèle Flash v1.5, ultra-rapide, économique et parfait pour la vision + texte
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def describe_dish_from_bytes(self, b64_data):
        """Gemini regarde la photo brute en haute qualité et l'analyse"""
        try:
            raw_bytes = base64.b64decode(b64_data)
            response = self.model.generate_content([
                {"mime_type": "image/jpeg", "data": raw_bytes},
                "Analyse cette photo de plat de restaurant. Décris brièvement ce que c'est, ses ingrédients visibles et son aspect culinaire (gourmand, croustillant, frais, coloré) pour un menu."
            ])
            return response.text.strip()
        except Exception as e:
            # Fallback amical pour éviter le crash de l'application
            return f"Un magnifique plat signature préparé avec passion par notre chef. (Erreur diagnostic: {str(e)})"

    def generate_facebook_caption(self, description):
        """Gemini rédige la légende commerciale pour Facebook & Insta"""
        try:
            prompt = f"En t'appuyant sur cette description de plat : '{description}', rédige une légende captivante, chaleureuse et vendeuse pour les réseaux sociaux d'un restaurant. Donne faim, utilise un ton professionnel et convivial de restaurateur qui s'adresse à ses clients fidèles. Ne parle pas de réservations ou de numéro de téléphone dans ton texte, le reste de l'application s'en charge automatiquement."
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "Une nouvelle création gourmande vient de sortir des cuisines ! Un pur délice à venir découvrir dès aujourd'hui à notre table. Éveillez vos papilles ! ✨"

    def generate_hashtags(self, description):
        """Gemini génère le bloc de hashtags pertinents"""
        try:
            prompt = f"Génère une seule ligne contenant entre 5 et 8 hashtags culinaires pertinents, branchés et séparés par des espaces, basés sur cette description : '{description}'."
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "#restaurant #instafood #faitmaison #gastronomie #chef #suggestions"
