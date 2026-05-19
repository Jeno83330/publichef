import os
import traceback
from PIL import Image, ImageFilter
from rembg import remove, new_session

class GeminiEngine:
    def __init__(self):
        print("[VISUAL ENGINE] Initialisation du moteur...")
        self.session = new_session("u2netp")

    def compose_dish_in_environment(self, dish_img_path, env_img_path):
        try:
            print("[VISUAL ENGINE] 1. Ouverture des images...")
            dish = Image.open(dish_img_path).convert("RGBA")
            env = Image.open(env_img_path).convert("RGBA")
            
            # 🚀 L'OPTIMISATION EXTRÊME : On réduit à 500px pour sauver le CPU de Render
            print("[VISUAL ENGINE] 2. Compression extrême pour le CPU...")
            dish.thumbnail((500, 500), Image.Resampling.LANCZOS)
            
            print("[VISUAL ENGINE] 3. Lancement de l'IA Rembg (Patientez 10 à 20s)...")
            dish_cutout = remove(dish, session=self.session)
            print("[VISUAL ENGINE] 4. Détourage réussi ! Assemblage géométrique...")
            
            target_width = int(env.width * 0.55)
            ratio = target_width / dish_cutout.width
            target_height = int(dish_cutout.height * ratio)
            dish_resized = dish_cutout.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            perspective_height = int(target_height * 0.85)
            dish_perspective = dish_resized.resize((target_width, perspective_height), Image.Resampling.LANCZOS)
            
            shadow = Image.new("RGBA", dish_perspective.size, (0, 0, 0, 0))
            shadow_mask = dish_perspective.getchannel('A')
            shadow.putalpha(shadow_mask)
            
            shadow_data = shadow.getdata()
            new_shadow_data = [(0, 0, 0, int(a * 0.6)) if a > 0 else (0, 0, 0, 0) for r, g, b, a in shadow_data]
            shadow.putdata(new_shadow_data)
            
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))
            
            paste_x = (env.width - target_width) // 2
            paste_y = int(env.height * 0.45)
            
            env.paste(shadow, (paste_x, paste_y + 20), shadow)
            env.paste(dish_perspective, (paste_x, paste_y), dish_perspective)
            
            output_path = dish_img_path.parent / "composed.jpg"
            final_image = env.convert("RGB")
            final_image.save(output_path, "JPEG", quality=85)
            
            print("[VISUAL ENGINE] 5. Succès Total ! Image sauvegardée.")
            return str(output_path)
            
        except Exception as e:
            print(f"\n[VISUAL ENGINE ERROR] : {traceback.format_exc()}\n")
            return str(dish_img_path)
