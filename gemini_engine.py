import os
from pathlib import Path
from PIL import Image, ImageFilter

class GeminiEngine:
    def __init__(self):
        # Prêt pour de futures intégrations
        pass

    def compose_dish_in_environment(self, dish_path, env_path):
        output_path = Path("uploads") / "composed_final.jpg"
        
        try:
            # 1. Préparer le décor (fond de salle ou terrasse)
            with Image.open(env_path) as bg:
                bg = bg.convert("RGBA")
                # Format carré parfait pour Instagram/Facebook (1200x1200)
                bg = bg.resize((1200, 1200), Image.Resampling.LANCZOS)
                # Effet Bokeh pro : on floute le fond pour faire ressortir l'assiette
                bg = bg.filter(ImageFilter.GaussianBlur(radius=8))

            # 2. Préparer l'assiette détourée
            with Image.open(dish_path) as dish:
                dish = dish.convert("RGBA")
                
                # Taille idéale : l'assiette prend 75% de l'image
                target_size = int(1200 * 0.75)
                ratio = min(target_size / dish.width, target_size / dish.height)
                new_w = int(dish.width * ratio)
                new_h = int(dish.height * ratio)
                
                dish = dish.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # 3. Centrage mathématique parfait
                offset_x = (1200 - new_w) // 2
                offset_y = (1200 - new_h) // 2

                # 4. Fusionner l'assiette sur le fond
                bg.paste(dish, (offset_x, offset_y), dish)
                
                # 5. Sauvegarder le résultat final
                final_image = bg.convert("RGB")
                final_image.save(output_path, "JPEG", quality=95)
                
                return str(output_path)
                
        except Exception as e:
            print(f"[ERROR COMPOSITION] : {str(e)}")
            # En cas de crash, on renvoie l'assiette brute pour ne pas bloquer l'appli
            return str(dish_path)
