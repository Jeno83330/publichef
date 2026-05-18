import os
import google.generativeai as genai

class AIEngine:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # Double rideau : Modèle principal lourd vs Modèle Flash ultra-rapide anti-surcharge
        self.primary_model = "gemini-1.5-pro"
        self.backup_model = "gemini-2.5-flash"

    def _call_with_fallback(self, prompt, contents_meta=None):
        """Logique générique de bascule automatique si le modèle principal rame ou sature."""
        payload = [prompt]
        if contents_meta:
            payload.insert(0, contents_meta)

        try:
            model = genai.GenerativeModel(model_name=self.primary_model)
            # Timeout serré à 10s pour ne pas faire attendre l'iPhone
            response = model.generate_content(payload, request_options={"timeout": 10})
            return response.text
        except Exception as e:
            print(f"[WARN AI_ENGINE] Principal ({self.primary_model}) indisponible : {str(e)}. Bascule immédiate.")
            model_backup = genai.GenerativeModel(model_name=self.backup_model)
            response_backup = model_backup.generate_content(payload, request_options={"timeout": 10})
            return response_backup.text

    def describe_dish_from_bytes(self, img_b64):
        import base64
        image_data = base64.b64decode(img_b64)
        contents_meta = {"mime_type": "image/jpeg", "data": image_data}
        
        prompt = (
            "Analyse cette photo de plat. Donne une description culinaire ultra-précise, "
            "gastronomique et vendeuse du plat (ingrédients, textures, cuisson)."
        )
        return self._call_with_fallback(prompt, contents_meta)

    def generate_facebook_caption(self, description):
        prompt = (
            f"En utilisant cette description du plat : '{description}', rédige une légende captivante "
            f"pour Facebook et Instagram. Le ton doit être chaleureux, pro, axé cuisine maison et produits frais. "
            f"Ajoute des émojis locaux et une invitation claire à réserver. Ne mets pas le numéro de téléphone ici."
        )
        return self._call_with_fallback(prompt)

    def generate_hashtags(self, description):
        prompt = (
            f"Génère une ligne de 8 hashtags pertinents et optimisés pour les réseaux sociaux, "
            f"séparés par des espaces, basés sur ce plat : '{description}'. "
            f"Inclus obligatoirement #LaCiotat et des tags culinaires pros."
        )
        return self._call_with_fallback(prompt)
