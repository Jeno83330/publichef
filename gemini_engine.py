import os
import requests
import traceback
from io import BytesIO
from PIL import Image, ImageFilter

class GeminiEngine:
    def __init__(self):
        self.api_key = os.getenv("REMOVE_BG_API_KEY")
        print("[VISUAL ENGINE PRO] Initialisation du moteur de détourage externe")

    def compose_dish_in_environment(self, dish_img_path, env_img_path):
        try:
            if not self.api_key:
                print("[VISUAL ENGINE ERROR] Clé REMOVE_BG_API_KEY introuvable.")
                return str(dish_img_path)

            print("[VISUAL ENGINE PRO] 1. Envoi de l'image à l'API Remove.bg...")
            
            with open(dish_img_path, 'rb') as f:
                response = requests.post(
                    'https://api.remove.bg/v1.0/removebg',
                    files={'image_file': f},
                    data={'size': 'auto'},
                    headers={'X-Api-Key': self.api_key},
                    timeout=15
                )
            
            if response.status_code != 200:
                print(f"[VISUAL ENGINE ERROR] Erreur API (Code {response.status_code}) : {response.text}")
                return self._fallback_composition(dish_img_path, env_img_path)

            print("[VISUAL ENGINE PRO] 2. Détourage réussi. Traitement graphique et perspective...")
            
            dish_cutout = Image.open(BytesIO(response.content)).convert("RGBA")
            
            with Image.open(env_img_path).convert("RGBA") as env:
                # --- L'assiette passe à 75% de la largeur ---
                target_width = int(env.width * 0.75) 
                ratio = target_width / dish_cutout.width
                target_height = int(dish_cutout.height * ratio)
                dish_resized = dish_cutout.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                perspective_height = int(target_height * 0.85)
                dish_perspective = dish_resized.resize((target_width, perspective_height), Image.Resampling.LANCZOS)
                
                shadow = Image.new("RGBA", dish_perspective.size, (0, 0, 0, 0))
                shadow_mask = dish_perspective.getchannel('A')
                shadow.putalpha(shadow_mask)
                
                shadow_data = shadow.getdata()
                new_shadow_data = [(0, 0, 0, int(a * 0.5)) if a > 0 else (0, 0, 0, 0) for r, g, b, a in shadow_data]
                shadow.putdata(new_shadow_data)
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))
                
                paste_x = (env.width - target_width) // 2
                # --- On la remonte légèrement (0.40 au lieu de 0.45) pour compenser la taille ---
                paste_y = int(env.height * 0.40) 
                
                env.paste(shadow, (paste_x, paste_y + 15), shadow)
                env.paste(dish_perspective, (paste_x, paste_y), dish_perspective)
                
                output_path = dish_img_path.parent / "composed.jpg"
                final_image = env.convert("RGB")
                final_image.save(output_path, "JPEG", quality=90)
            
            print("[VISUAL ENGINE PRO] 3. Montage finalisé avec succès.")
            return str(output_path)
            
        except Exception as e:
            print(f"\n[VISUAL ENGINE CRITICAL ERROR] :\n{traceback.format_exc()}\n")
            return self._fallback_composition(dish_img_path, env_img_path)

    def _fallback_composition(self, dish_img_path, env_img_path):
        try:
            with Image.open(env_img_path).convert("RGB") as env:
                with Image.open(dish_img_path).convert("RGB") as dish:
                    dish.thumbnail((300, 300))
                    env.paste(dish, (20, 20))
                    output_path = dish_img_path.parent / "composed.jpg"
                    env.save(output_path, "JPEG", quality=80)
            return str(output_path)
        except:
            return str(dish_img_path)
