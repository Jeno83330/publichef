import os
import traceback
from PIL import Image, ImageFilter
from rembg import remove

class GeminiEngine:
    def __init__(self):
        print("[VISUAL ENGINE] Initialisation du moteur de fusion local (Rembg + PIL)")

    def compose_dish_in_environment(self, dish_img_path, env_img_path):
        try:
            print("[VISUAL ENGINE] Début du détourage et de la fusion...")
            
            # 1. Ouverture des images en mode transparent (RGBA)
            dish = Image.open(dish_img_path).convert("RGBA")
            env = Image.open(env_img_path).convert("RGBA")
            
            # 2. Détourage chirurgical de l'assiette (Suppression de la nappe rouge)
            dish_cutout = remove(dish)
            
            # 3. Mise à l'échelle (L'assiette occupera 55% de la largeur de la table)
            target_width = int(env.width * 0.55)
            ratio = target_width / dish_cutout.width
            target_height = int(dish_cutout.height * ratio)
            dish_resized = dish_cutout.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # 4. Perspective fuyante (On écrase la hauteur de 15% pour qu'elle semble posée à plat)
            perspective_height = int(target_height * 0.85)
            dish_perspective = dish_resized.resize((target_width, perspective_height), Image.Resampling.LANCZOS)
            
            # 5. Création d'une ombre portée ultra-réaliste
            shadow = Image.new("RGBA", dish_perspective.size, (0, 0, 0, 0))
            shadow_mask = dish_perspective.getchannel('A')
            shadow.putalpha(shadow_mask)
            
            # Opacité de l'ombre à 60%
            shadow_data = shadow.getdata()
            new_shadow_data = [(0, 0, 0, int(a * 0.6)) if a > 0 else (0, 0, 0, 0) for r, g, b, a in shadow_data]
            shadow.putdata(new_shadow_data)
            
            # Flou de l'ombre pour la douceur
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))
            
            # 6. Centrage géométrique sur la table en bois
            paste_x = (env.width - target_width) // 2
            paste_y = int(env.height * 0.45) # Centré, légèrement vers le bas de l'image
            
            # 7. Assemblage des couches (Décor + Ombre décalée + Assiette)
            env.paste(shadow, (paste_x, paste_y + 20), shadow)
            env.paste(dish_perspective, (paste_x, paste_y), dish_perspective)
            
            # 8. Exportation en JPEG pour Facebook
            output_path = dish_img_path.parent / "composed.jpg"
            final_image = env.convert("RGB")
            final_image.save(output_path, "JPEG", quality=95)
            
            print("[VISUAL ENGINE] Succès ! Image fusionnée et sauvegardée.")
            return str(output_path)
            
        except Exception as e:
            print(f"\n[VISUAL ENGINE ERROR] : {traceback.format_exc()}\n")
            return str(dish_img_path)
