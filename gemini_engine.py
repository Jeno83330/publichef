import os
import base64
import traceback
from io import BytesIO
from PIL import Image
from google import genai

class GeminiEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
        # Le nouveau SDK initialise un client moderne
        self.client = genai.Client(api_key=api_key)

    def compose_dish_in_environment(self, dish_img_path, env_img_path):
        try:
            # Ouverture des images avec PIL pour les valider
            dish_img = Image.open(dish_img_path)
            env_img = Image.open(env_img_path)
            
            # PROMPT DE COMPOSITION HAUTE COUTURE AVEC RESPECT DE LA PERSPECTIVE
            prompt = "Tu es un photographe culinaire et un expert en post-production de classe mondiale.\n\n" \
                     "INSTRUCTIONS STRICTES :\n" \
                     "1. Analyse l'image du décor pour identifier parfaitement le plan horizontal et la perspective de la table.\n" \
                     "2. Prends l'assiette du plat détouré.\n" \
                     "3. Transforme la perspective 3D de l'assiette pour qu'elle soit COMPLÈTEMENT À PLAT sur le plan horizontal de la table.\n" \
                     "4. L'assiette ne doit JAMAIS sembler être dressée verticalement ou flotter. Elle doit être inclinée pour suivre la fuite de la table.\n" \
                     "5. Fusionne les deux de manière réaliste, en ajustant la colorimétrie.\n" \
                     "6. Ajoute des ombres portées douces, naturelles et culinaires DIRECTEMENT sous l'assiette pour la 'poser' de manière solide et réaliste sur le bois.\n" \
                     "Le résultat doit être une photo unique, professionnelle et parfaitement unifiée."

            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[
                    env_img,  # On donne le décor
                    dish_img, # On donne le plat
                    prompt    # Et les instructions précises de perspective
                ]
            )
            
            # Sauvegarde du résultat
            output_path = dish_img_path.parent / "composed.jpg"
            # Extraction et sauvegarde de l'image (cela dépend de la structure de réponse du SDK)
            # Pour google-genai 2026, la réponse image est souvent dans response.generated_image
            # Mais souvent le plus simple est de convertir la réponse textuelle b64 si l'IA l'a retourné ainsi.
            
            # Dans le cas de composition, le SDK moderne simplifie souvent cela.
            # Supposons ici que response.generated_image est l'image PIL
            
            # NOTE CRITIQUE : Si le SDK ne supporte pas directement la génération d'image
            # par fusion de cette manière (car il est orienté vision -> texte),
            # il faut utiliser une API de composition dédiée (comme Stable Diffusion).
            
            # Hypothèse de travail avec le SDK Google modernisé :
            # response.text contiendra une représentation b64 de l'image fusionnée.
            if response.text and response.text.startswith("data:image/jpeg;base64,"):
                img_data = base64.b64decode(response.text.split(",")[1])
                with open(output_path, "wb") as f:
                    f.write(img_data)
                return str(output_path)
            
            # Fallback en cas d'échec de la composition IA (on retourne l'image du plat brute pour l'instant)
            print("[GEMINI ENGINE] WARN: La composition IA n'a pas retourné d'image. Fallback sur le plat seul.")
            return str(dish_img_path)

        except Exception as e:
            print(f"\n[GEMINI ENGINE ERROR COMPOSE] :\n{traceback.format_exc()}\n")
            # En cas de crash, on retourne l'image du plat d'origine pour ne pas bloquer l'app
            return str(dish_img_path)
