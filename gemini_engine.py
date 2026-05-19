import os
import json
import base64
import traceback
from io import BytesIO
from PIL import Image
from google.cloud import aiplatform

class GeminiEngine:
    def __init__(self):
        self.project = os.getenv("PROJECT_ID", "publi-chef")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        # Authentification dynamique via la variable d'environnement JSON
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if credentials_json:
            try:
                cred_dict = json.loads(credentials_json)
                cred_path = "/tmp/google_creds.json"
                with open(cred_path, "w") as f:
                    json.dump(cred_dict, f)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
                print("[GEMINI VISUAL] Authentification par clé JSON configurée avec succès.")
            except Exception as e:
                print(f"[GEMINI VISUAL ERROR] Impossible de charger le JSON : {str(e)}")
        
        aiplatform.init(project=self.project, location=self.location)

    def compose_dish_in_environment(self, dish_img_path, env_img_path):
        try:
            # Conversion du décor en Base64 pour l'API Imagen (Inpainting / Edition)
            with open(env_img_path, "rb") as f:
                env_b64 = base64.b64encode(f.read()).decode("utf-8")

            # On passe aussi le plat en Base64 pour qu'il soit analysé par l'API graphique
            with open(dish_img_path, "rb") as f:
                dish_b64 = base64.b64encode(f.read()).decode("utf-8")

            # Endpoint direct d'Imagen 3 Image Generation / Editing
            endpoint = f"projects/{self.project}/locations/{self.location}/publishers/google/models/imagegeneration@006"
            
            prompt = (
                "Prends l'assiette du plat et incruste-la de manière parfaitement réaliste sur la table en bois du décor. "
                "Modifie l'inclinaison de l'assiette et applique une perspective fuyante pour qu'elle semble posée bien à plat "
                "naturellement sur le bois. Adapte l'échelle de l'assiette pour qu'elle occupe une place centrale et cohérente. "
                "Harmonise parfaitement la lumière et ajoute une ombre portée douce sous l'assiette."
            )
            
            # Format d'instance universel et ultra-stable (dictionnaire brut pour éviter l'AttributeError)
            instances = [
                {
                    "prompt": prompt,
                    "image": {"bytesBase64Encoded": env_b64}
                }
            ]
            
            parameters = {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "outputMimeType": "image/jpeg"
            }
            
            # Appel direct via le client générique de prédiction
            client = aiplatform.gapic.PredictionServiceClient(
                client_options={"api_endpoint": f"{self.location}-aiplatform.googleapis.com"}
            )
            
            print("[GEMINI VISUAL] Envoi de la demande de fusion à Imagen...")
            response = client.predict(endpoint=endpoint, instances=instances, parameters=parameters)
            
            output_path = dish_img_path.parent / "composed.jpg"
            
            for prediction in response.predictions:
                if "bytesBase64Encoded" in prediction:
                    img_data = base64.b64decode(prediction["bytesBase64Encoded"])
                    with open(str(output_path), "wb") as f:
                        f.write(img_data)
                    print("[GEMINI VISUAL] Succès total ! Image fusionnée et enregistrée.")
                    return str(output_path)
            
            print("[GEMINI VISUAL WARNING] Pas de b64 trouvé dans la réponse, utilisation du fallback.")
            return str(dish_img_path)

        except Exception as e:
            print(f"\n[GEMINI VISUAL ERROR COMPOSE] :\n{traceback.format_exc()}\n")
            return str(dish_img_path)
