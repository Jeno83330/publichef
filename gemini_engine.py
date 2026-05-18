import os
from genai import Client
from genai import types

class GeminiEngine:
    def __init__(self):
        # La nouvelle bibliothèque utilise automatiquement la variable GEMINI_API_KEY
        self.client = Client()
        self.model = "gemini-2.5-flash"

    def compose_dish_in_environment(self, dish_path, env_path):
        from PIL import Image
        import io

        print(f"[IMAGE ENGINE 2.5] Connexion au modèle de pointe : {self.model}")
        
        # Ouverture propre des images avec Pillow
        dish_img = Image.open(dish_path)
        env_img = Image.open(env_path)

        prompt = (
            "Prends le plat de la première image, détoure-le proprement sans aucun résidu, "
            "et place-le de manière réaliste au centre sur la table de la deuxième image. "
            "Ajuste l'ombre sous l'assiette et la perspective à 45 degrés pour une intégration parfaite. "
            "Renvoie uniquement l'image finale combinée au format JPEG."
        )

        try:
            # Nouvelle syntaxe officielle de la bibliothèque google-genai
            response = self.client.models.generate_content(
                model=self.model,
                contents=[dish_img, env_img, prompt],
                config=types.GenerateContentConfig(
                    mime_type="image/jpeg"
                )
            )
            
            # Sauvegarde du résultat
            output_path = os.path.dirname(dish_path) + "/last_composed.jpg"
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        with open(output_path, "wb") as f_out:
                            f_out.write(part.inline_data.data)
                        return output_path
            
            raise Exception("L'API moderne n'a pas retourné de bloc d'image brut.")
            
        except Exception as e:
            print(f"[CRITICAL IMAGE ENGINE 2.5] Échec du traitement : {str(e)}")
            raise e
