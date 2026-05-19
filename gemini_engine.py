import os
import requests
import traceback
from PIL import Image, ImageFilter

class GeminiEngine:
    def __init__(self):
        self.api_key = os.getenv("REMOVE_BG_API_KEY")
        print("[VISUAL ENGINE] Initialisation du moteur ultra-rapide Remove.bg API")

    def compose_dish_in_environment(self, dish_img_path, env_img_path):
        try:
            if not self.api_key:
                print("[VISUAL ENGINE ERROR] Clé REMOVE_BG_API_KEY manquante dans Render !")
                return str(dish_img_path)

            print("[VISUAL ENGINE] 1. Envoi de l'assiette à l'API Remove.bg...")
            
            # Appel à l'API externe (Zéro effort pour le CPU de Render)
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': open(dish_img_path, 'rb')},
                data={'size': 'auto'},
                headers={'X-Api-Key': self.api_key},
            )
            
            if response.status_code != 200:
                print(f"[VISUAL ENGINE ERROR] Erreur API Remove.bg : {response.text}")
                return str(dish_img_path)

            print("[VISUAL ENGINE] 2. Détourage réussi en 2 secondes ! Assemblage graphique...")
            
            # On récupère l'assiette détourée proprement
            dish_cutout = Image.open(requests.utils.io.BytesIO(response.content)).convert("RGBA")
            env = Image.open(env_img_path).convert("RGBA")
            
            # Redimensionnement (55% de la table)
            target_width = int(env.width * 0.55)
            ratio = target_width / dish_cutout.width
            target_height = int(dish_cutout.height * ratio)
            dish_resized = dish_cutout.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Perspective (Écrasement à plat)
            perspective_height = int(target_height * 0.85)
            dish_perspective = dish_resized.resize((target_width, perspective_height), Image.Resampling.LANCZOS)
            
            # Ombre portée
            shadow = Image.new("RGBA", dish_perspective.size, (0, 0, 0, 0))
            shadow_mask = dish_perspective.getchannel('A')
            shadow.putalpha(shadow_mask)
            
            shadow_data = shadow.getdata()
            new_shadow_data = [(0, 0, 0, int(a * 0.5)) if a > 0 else (0, 0, 0, 0) for r, g, b, a in shadow_data]
            shadow.putdata(new_shadow_data)
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))
            
            # Positionnement sur la table en bois
            paste_x = (env.width - target_width) // 2
            paste_y = int(env.height * 0.45)
            
            # Collage
            env.paste(shadow, (paste_x, paste_y + 15), shadow)
            env.paste(dish_perspective, (paste_x, paste_y), dish_perspective)
            
            # Sauvegarde finale
            output_path = dish_img_path.parent / "composed.jpg"
            final_image = env.convert("RGB")
            final_image.save(output_path, "JPEG", quality=90)
            
            print("[VISUAL ENGINE] 3. Montage terminé avec succès !")
            return str(output_path)
            
        except Exception as e:
            print(f"\n[VISUAL ENGINE ERROR] : {traceback.format_exc()}\n")
            return str(dish_img_path)
