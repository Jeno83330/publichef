import os
from genai import Client
from genai import types

class GeminiEngine:
    def __init__(self):
        self.client = Client()
        self.model = "gemini-2.5-flash"

    def compose_dish_in_environment(self, dish_path, env_path):
        from PIL import Image
        import io

        print(f"[IMAGE ENGINE 2.5] Traitement avec le modèle de pointe : {self.model}")
        
        dish_img = Image.open(dish_path)
        env_img = Image.open(env_path)

        prompt = (
            "Prends le plat de la première image, détoure-le proprement sans aucun résidu, "
            "et place-le de manière réaliste au centre sur la table de la deuxième image. "
            "Ajuste l'ombre sous l'assiette et la perspective à 45 degrés pour une intégration parfaite. "
            "Renvoie uniquement l'image finale combinée au format JPEG."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[dish_img, env_img, prompt],
                config=types.GenerateContentConfig(
                    mime_type="image/jpeg"
                )
            )
            
            output_path = os.path.dirname(dish_path) + "/last_composed.jpg"
            
            # --- Nouvelle méthode d'extraction standard pour Gemini 2.5 ---
            # On vérifie d'abord si on peut récupérer les octets générés directement
            try:
                generated_bytes = response.generated_bytes
                if generated_bytes:
                    with open(output_path, "wb") as f_out:
                        f_out.write(generated_bytes)
                    return output_path
            except AttributeError:
                pass

            # Si non, on extrait via les parts de manière moderne
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Sur l'API moderne, la donnée est souvent directement dans part.inline_data.data ou accessible par les octets
                    data = None
                    if hasattr(part, 'inline_data') and part.inline_data:
                        data = part.inline_data.data
                    elif hasattr(part, 'text') and not part.text:
                        # Parfois les données d'image se trouvent dans les octets de la part
                        data = part.bytes

                    if data:
                        with open(output_path, "wb") as f_out:
                            f_out.write(data)
                        return output_path
            
            raise Exception("Impossible d'extraire les données binaires de l'image de la réponse.")
            
        except Exception as e:
            print(f"[CRITICAL IMAGE ENGINE 2.5] Échec du traitement : {str(e)}")
            raise e
