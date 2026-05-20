import os
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO

class GeminiEngine:
    def __init__(self):
        # On vérifie les deux orthographes possibles de dimanche !
        self.removebg_api_key = os.environ.get("REMOVE_BG_API_KEY") or os.environ.get("REMOVEBG_API_KEY")

    def compose_dish_in_environment(self, dish_path, env_path):
        output_path = Path("uploads") / "composed_final_pro.jpg"
        
        try:
            if not self.removebg_api_key:
                print("[WARNING] Clé Remove.bg manquante. Retour image brute.")
                return str(dish_path)

            # 1. ENVOI À L'API PRO POUR DÉTOURAGE
            with open(dish_path, 'rb') as file:
                response = requests.post(
                    'https://api.remove.bg/v1.0/removebg',
                    files={'image_file': file},
                    data={'size': 'auto'},
                    headers={'X-Api-Key': self.removebg_api_key},
                )
            
            if response.status_code != 200:
                print(f"[ERROR API DETOURAGE] : {response.text}")
                return str(dish_path)
            
            # L'image détourée (fond transparent)
            dish_transparent = Image.open(BytesIO(response.content)).convert("RGBA")

            # 2. PRÉPARATION DU DÉCOR
            with Image.open(env_path) as bg:
                bg = bg.convert("RGBA")
                
                # 3. REDIMENSIONNEMENT ET CENTRAGE (L'assiette prend 70% de la largeur)
                bg_w, bg_h = bg.size
                target_size = int(bg_w * 0.70)
                dish_w, dish_h = dish_transparent.size
                ratio = target_size / dish_w
                new_h = int(dish_h * ratio)
                
                dish_resized = dish_transparent.resize((target_size, new_h), Image.Resampling.LANCZOS)
                
                pos_x = (bg_w - target_size) // 2
                pos_y = (bg_h - new_h) // 2
                
                # 4. FUSION PARFAITE
                bg.paste(dish_resized, (pos_x, pos_y), dish_resized)
                
                # 5. SAUVEGARDE FINALE
                final_image = bg.convert("RGB")
                final_image.save(output_path, "JPEG", quality=95)
                return str(output_path)
                
        except Exception as e:
            print(f"[ERROR STUDIO PRO] : {str(e)}")
            return str(dish_path)
