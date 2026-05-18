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

        print(f"[IMAGE ENGINE 2.5] Traitement avec le modèle : {self.model}")
        
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
            
            # Technique de secours universelle : analyse de l'objet response complet
            # 1. Tentative par les octets directs du modèle 2.5
            if hasattr(response, 'generated_bytes') and response.generated_bytes:
                with open(output_path, "wb") as f_out:
                    f_out.write(response.generated_bytes)
                return output_path

            # 2. Extraction via les structures de texte ou d'inline data de secours
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                
                # Récupération des données binaires peu importe l'attribut nommé par Google
                data = None
                for attr in ['inline_data', 'bytes', 'data']:
                    if hasattr(part, attr) and getattr(part, attr):
                        val = getattr(part, attr)
                        data = val.data if hasattr(val, 'data') else val
                        break
                
                if data and isinstance(data, bytes):
                    with open(output_path, "wb") as f_out:
                        f_out.write(data)
                    return output_path

            # 3. Si Google renvoie exceptionnellement un format structuré par erreur, on extrait le texte brut
            if response.text:
                print("[WARN] Données reçues sous forme de texte, tentative de conversion...")
                raise Exception("L'API a renvoyé du texte au lieu d'une image JPEG.")
                
            raise Exception("Aucun flux binaire d'image détecté dans la réponse Gemini 2.5.")
            
        except Exception as e:
            print(f"[CRITICAL IMAGE ENGINE 2.5] Échec : {str(e)}")
            raise e
