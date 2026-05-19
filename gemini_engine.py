import os
import json
import base64
import traceback
from io import BytesIO
from PIL import Image
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict

class GeminiEngine:
    def __init__(self):
        self.project = os.getenv("PROJECT_ID", "publi-chef")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        # Authentification dynamique via la variable d'environnement JSON
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if credentials_json:
            try:
                cred_dict = json.loads(credentials_json)
                # Création d'un fichier temporaire sécurisé pour que le SDK Google puisse le lire
                cred_path = "/tmp/google_creds.json"
                with open(cred_path, "w") as f:
                    json.dump(cred_dict, f)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
                print("[GEMINI VISUAL] Authentification par clé JSON configurée avec succès.")
            except Exception as e:
                print(f"[GEMINI VISUAL ERROR] Impossible de charger le JSON des identifiants : {str(e)}")
        
        # Initialisation de Vertex AI
        aiplatform.init(project=self.project, location=self.location)

    def compose_dish_in_environment(self, dish_img_path, env_img_path):
        try:
            # Ouverture et préparation des images
            dish_img = Image.open(dish_img_path)
            env_img = Image.open(env_img_path)
            
            # Conversion en Base64 pour l'envoi à l'API de génération graphique
            with open(dish_img_path, "rb") as f:
                dish_b64 = base64.b64encode(f.read()).decode("utf-8")
            with open(env_img_path, "rb") as f:
                env_b64 = base64.b64encode(f.read()).decode("utf-8")

            # Utilisation du endpoint officiel d'édition d'image (Imagen 3 / imagegeneration)
            endpoint = f"projects/{self.project}/locations/{self.location}/publishers/google/models/imagegeneration@006"
            
            prompt = (
                "Prends l'assiette du plat présente sur l'image du plat et incruste-la de manière parfaitement "
                "réaliste sur la table en bois de l'image de décor. Modifie l'inclinaison et applique la perspective fuyante "
                "pour que l'assiette semble posée à plat naturellement sur la table. Harmonise la lumière et les reflets, "
                "et ajoute une ombre portée douce et réaliste sous l'assiette. Le résultat final doit être une seule image propre."
            )
            
            instances = [
                predict.instance.ImageGenerationPredictionInstance(
                    prompt=prompt,
                    image={"bytesBase64Encoded": env_b64},
                )
            ]
            
            parameters = predict.params.ImageGenerationPredictionParams(
                sampleCount=1,
                model_version="imagegeneration@006",
            )
            
            # Appel au service de prédiction graphique de Google Cloud
            client = aiplatform.gapic.PredictionServiceClient(
                client_options={"api_endpoint": f"{self.location}-aiplatform.googleapis.com"}
            )
            response = client.predict(endpoint=endpoint, instances=instances, parameters=parameters)
            
            output_path = dish_img_path.parent / "composed.jpg"
            
            for prediction in response.predictions:
                if "bytesBase64Encoded" in prediction:
                    img_data = base64.b64decode(prediction["bytesBase64Encoded"])
                    with open(str(output_path), "wb") as f:
                        f.write(img_data)
                    print("[GEMINI VISUAL] Fusion d'image réussie avec succès via l'API Imagen.")
                    return str(output_path)
            
            print("[GEMINI VISUAL] Aucune donnée image renvoyée par l'API, utilisation du fallback.")
            return str(dish_img_path)

        except Exception as e:
            print(f"\n[GEMINI VISUAL ERROR COMPOSE] :\n{traceback.format_exc()}\n")
            return str(dish_img_path)
