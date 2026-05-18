import os
import google.generativeai as genai

class GeminiEngine:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # Utilisation des alias officiels stables et mis à jour par Google
        self.primary_model = "gemini-1.5-pro-latest"
        self.backup_model = "gemini-1.5-flash-latest"

    def compose_dish_in_environment(self, dish_path, env_path):
        from PIL import Image
        import os

        with open(str(dish_path), "rb") as f:
            dish_data = f.read()
        with open(str(env_path), "rb") as f:
            env_data = f.read()

        prompt = (
            "Prends le plat de la première image, détoure-le proprement, "
            "et place-le de manière réaliste au centre sur la table de la deuxième image. "
            "Ajuste l'ombre sous l'assiette et la perspective à 45 degrés. "
            "Renvoie uniquement l'image finale combinée au format JPEG."
        )

        contents = [
            {"mime_type": "image/jpeg", "data": dish_data},
            {"mime_type": "image/jpeg", "data": env_data},
            prompt
        ]

        # --- TENTATIVE 1 : MODÈLE PRO ---
        try:
            print(f"[IMAGE ENGINE] Essai modèle principal : {self.primary_model}")
            model = genai.GenerativeModel(model_name=self.primary_model)
            response = model.generate_content(contents, request_options={"timeout": 12})
            
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    output_path = os.path.dirname(dish_path) + "/last_composed.jpg"
                    with open(output_path, "wb") as f_out:
                        f_out.write(part.inline_data.data)
                    return output_path
        except Exception as e:
            print(f"[WARN IMAGE ENGINE] Échec Pro ({self.primary_model}) : {str(e)}. Bascule Flash immédiate.")

        # --- TENTATIVE 2 : BASCULE FLASH ---
        print(f"[IMAGE ENGINE] Lancement du modèle Flash : {self.backup_model}")
        model_backup = genai.GenerativeModel(model_name=self.backup_model)
        response_backup = model_backup.generate_content(contents, request_options={"timeout": 15})
        
        for part in response_backup.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                output_path = os.path.dirname(dish_path) + "/last_composed.jpg"
                with open(output_path, "wb") as f_out:
                    f_out.write(part.inline_data.data)
                return output_path
        
        raise Exception("Les deux modèles de détourage ont échoué.")
