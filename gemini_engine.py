import os
import requests
import traceback
from io import BytesIO
from PIL import Image, ImageFilter

class GeminiEngine:
    def __init__(self):
        self.api_key = os.getenv("REMOVE_BG_API_KEY")
        print("[VISUAL ENGINE SaaS] Initialisation du moteur de compositing universel")

    def compose_dish_in_environment(self, dish_img_path, env_img_path):
        try:
            if not self.api_key:
                print("[VISUAL ENGINE ERROR] Clé REMOVE_BG manquante.")
                return str(dish_img_path)

            print("[VISUAL ENGINE SaaS] 1. Détourage de haute précision...")
            with open(dish_img_path, 'rb') as f:
                response = requests.post(
                    'https://api.remove.bg/v1.0/removebg',
                    files={'image_file': f},
                    data={'size': 'auto', 'crop': 'true'}, # On demande à l'API de recadrer l'inutile
                    headers={'X-Api-Key': self.api_key},
                    timeout=20
                )
            
            if response.status_code != 200:
                return self._fallback_composition(dish_img_path, env_img_path)

            print("[VISUAL ENGINE SaaS] 2. Analyse mathématique de la forme de l'objet...")
            dish_cutout = Image.open(BytesIO(response.content)).convert("RGBA")
            
            # Recadrage strict sur les pixels non transparents (Bounding Box)
            bbox = dish_cutout.getbbox()
            if bbox:
                dish_cutout = dish_cutout.crop(bbox)
                
            orig_w, orig_h = dish_cutout.size
            aspect_ratio = orig_w / float(orig_h)
            
            with Image.open(env_img_path).convert("RGBA") as env:
                # Calcul de base : l'objet prend 65% de la largeur de la table
                target_width = int(env.width * 0.65)
                scale = target_width / orig_w
                target_height = int(orig_h * scale)
                
                dish_resized = dish_cutout.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # --- LE CERVEAU DYNAMIQUE ---
                # Si aspect_ratio > 1.2 (C'est un objet large : pizza, assiette) -> on simule une perspective
                # Si aspect_ratio <= 1.2 (C'est un objet haut : burger, boisson) -> on garde les vraies proportions
                if aspect_ratio > 1.2:
                    print("[VISUAL ENGINE SaaS] Objet plat détecté : Application d'une perspective de table.")
                    final_height = int(target_height * 0.70) # Écrasement léger et naturel
                else:
                    print("[VISUAL ENGINE SaaS] Objet en volume détecté : Conservation des proportions réelles.")
                    final_height = target_height
                    
                dish_final = dish_resized.resize((target_width, final_height), Image.Resampling.LANCZOS)
                
                # --- GÉNÉRATION DE L'OMBRE UNIVERSELLE ---
                # L'ombre s'adapte à la largeur finale de l'objet
                shadow_width = int(target_width * 0.9)
                shadow_height = int(final_height * 0.2) if aspect_ratio > 1.2 else int(final_height * 0.1)
                
                shadow = Image.new("RGBA", (target_width, shadow_height), (0, 0, 0, 0))
                # Dessin d'une ellipse noire pure au centre
                from PIL import ImageDraw
                draw = ImageDraw.Draw(shadow)
                draw.ellipse([(target_width - shadow_width)//2, 0, target_width - (target_width - shadow_width)//2, shadow_height], fill=(0, 0, 0, 180))
                
                # Flou massif pour rendre l'ombre diffuse sur le bois
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))
                
                # --- POSITIONNEMENT ---
                paste_x = (env.width - target_width) // 2
                
                # Si c'est un objet haut (burger), on le descend un peu moins pour qu'il tienne debout
                base_y_offset = 0.50 if aspect_ratio > 1.2 else 0.40
                paste_y = int(env.height * base_y_offset)
                
                # L'ombre se place à la base exacte de l'objet
                shadow_y = paste_y + final_height - int(shadow_height * 0.6)
                
                # Fusion
                env.paste(shadow, (paste_x, shadow_y), shadow)
                env.paste(dish_final, (paste_x, paste_y), dish_final)
                
                output_path = dish_img_path.parent / "composed.jpg"
                final_image = env.convert("RGB")
                final_image.save(output_path, "JPEG", quality=90)
            
            print("[VISUAL ENGINE SaaS] 3. Montage universel terminé.")
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
