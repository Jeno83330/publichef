"""
app.py — Interface web PubliChef V2 (Version Production Intégration Directe Meta & Réservation Téléphone)
"""

import os
import io
import base64
import shutil
import traceback
import gc
import requests
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Récupération du Token Meta stocké sur Render
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

# Numéro de réservation officiel de L'Athélia
PHONE_RESERVATION = "04 42 08 65 28"

def convert_to_jpg(src, dst):
    try:
        with Image.open(str(src)) as im:
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.save(str(dst), "JPEG")
    except Exception:
        shutil.copy(str(src), str(dst))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/history_data")
def history_data():
    from history_manager import get_all_posts
    posts = get_all_posts()
    result = []
    for post in posts:
        img_path = Path(post["image"])
        if img_path.exists():
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            post["image_data"] = f"data:image/jpeg;base64,{img_b64}"
        result.append(post)
    return jsonify(result)


@app.route("/delete_post/<post_id>", methods=["DELETE"])
def delete_post(post_id):
    from history_manager import delete_post as dp
    success = dp(post_id)
    return jsonify({"success": success})


@app.route("/generate_v2", methods=["POST"])
def generate_v2():
    if "dish" not in request.files:
        return jsonify({"error": "La photo du plat est requise"}), 400

    dish_file = request.files["dish"]
    decor_name = request.form.get("decor", "salle")

    dish_raw = UPLOAD_FOLDER / "dish_raw"
    env_jpg = UPLOAD_FOLDER / "env.jpg"
    dish_jpg = UPLOAD_FOLDER / "dish.jpg"

    # 1. Enregistrement et conversion du plat
    dish_file.stream.seek(0)
    with open(str(dish_raw), "wb") as f:
        f.write(dish_file.stream.read())
    convert_to_jpg(dish_raw, dish_jpg)

    # 2. GESTION DU DÉCOR
    saved_decor_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    
    if "environment" in request.files and request.files["environment"].filename != '':
        env_file = request.files["environment"]
        env_raw = UPLOAD_FOLDER / "env_raw"
        env_file.stream.seek(0)
        with open(str(env_raw), "wb") as f:
            f.write(env_file.stream.read())
        convert_to_jpg(env_raw, env_jpg)
    elif saved_decor_path.exists():
        shutil.copy(str(saved_decor_path), str(env_jpg))
    else:
        return jsonify({"error": f"Aucun décor trouvé pour '{decor_name}'. Veuillez cliquer sur Modifier pour ajouter votre photo."}), 400

    try:
        from image_processor import ImageProcessor
        from gemini_engine import GeminiEngine
        from ai_engine import AIEngine

        processor = ImageProcessor()
        enhanced_dish = processor.enhance(dish_jpg)
        del processor
        gc.collect()

        gemini = GeminiEngine()
        composed_path = gemini.compose_dish_in_environment(
            enhanced_dish,
            env_jpg
        )
        del gemini
        gc.collect()

        with Image.open(composed_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            quality = 85
            while True:
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=quality)
                if len(buffer.getvalue()) <= 4 * 1024 * 1024 or quality < 30:
                    break
                quality -= 10
            compressed = buffer.getvalue()

        gc.collect()

        ai = AIEngine()
        img_b64 = base64.b64encode(compressed).decode("utf-8")
        
        last_output = UPLOAD_FOLDER / "last_output.jpg"
        with open(str(last_output), "wb") as f:
            f.write(compressed)
            
        del compressed
        description = ai.describe_dish_from_bytes(img_b64)
        instagram = ai.generate_instagram_caption(description)
        facebook = ai.generate_facebook_caption(description)
        
        # AJOUT DU BLOC DE RÉSERVATION AUTOMATIQUE SUR LE TEXTE FACEBOOK À L'ÉCRAN
        facebook_with_phone = f"{facebook}\n\n📞 Réservation : {PHONE_RESERVATION}"
        
        hashtags = ai.generate_hashtags(description)
        del ai
        gc.collect()

        from history_manager import save_post
        save_post(composed_path, description, instagram, facebook_with_phone, hashtags)

        return jsonify({
            "success": True,
            "description": description,
            "instagram": instagram,
            "facebook": facebook_with_phone,
            "hashtags": hashtags,
            "image": f"data:image/jpeg;base64,{img_b64}"
        })

    except Exception as e:
        gc.collect()
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/publish_to_socials", methods=["POST"])
def publish_to_socials():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Données invalides"}), 400

    share_fb = data.get("facebook", False)
    caption_fb = data.get("caption_fb", "")

    if not META_ACCESS_TOKEN or META_ACCESS_TOKEN == "":
        return jsonify({"success": False, "error": "Le jeton META_ACCESS_TOKEN n'est pas configuré sur Render."}), 400

    try:
        if share_fb:
            print("[META API] Envoi en cours vers la page Facebook...")
            
            image_path = UPLOAD_FOLDER / "last_output.jpg"
            if not image_path.exists():
                return jsonify({"success": False, "error": "Fichier image introuvable pour la publication."}), 400

            # Sécurité additionnelle : Si pour une raison ou une autre le numéro n'est pas écrit par l'utilisateur, l'API le rajoute de force à l'envoi
            if PHONE_RESERVATION not in caption_fb:
                caption_fb = f"{caption_fb}\n\n📞 Réservation : {PHONE_RESERVATION}"

            url = f"https://graph.facebook.com/v25.0/me/photos"
            payload = {
                'message': caption_fb,
                'access_token': META_ACCESS_TOKEN
            }
            
            with open(str(image_path), 'rb') as img_file:
                files = {
                    'source': ('post.jpg', img_file, 'image/jpeg')
                }
                response = requests.post(url, data=payload, files=files)
                res_data = response.json()

            if "error" in res_data:
                return jsonify({"success": False, "error": res_data["error"].get("message", "Erreur Facebook")}), 400
                
            print(f"[META API] Succès ! ID du Post Facebook : {res_data.get('id')}")

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/get_decors")
def get_decors():
    from decor_manager import get_all_decors_b64
    return jsonify(get_all_decors_b64())


@app.route("/save_decor/<decor_name>", methods=["POST"])
def save_decor_route(decor_name):
    from decor_manager import save_decor, get_all_decors_b64
    if "image" not in request.files:
        return jsonify({"error": "Pas d'image"}), 400
    file = request.files["image"]
    raw_path = UPLOAD_FOLDER / f"decor_{decor_name}_raw"
    jpg_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    file.stream.seek(0)
    with open(str(raw_path), "wb") as f:
        f.write(file.stream.read())
    convert_to_jpg(raw_path, jpg_path)
    save_decor(decor_name, jpg_path)
    return jsonify({"success": True, "decors": get_all_decors_b64()})


@app.route("/delete_decor/<decor_name>", methods=["DELETE"])
def delete_decor_route(decor_name):
    from decor_manager import delete_decor, get_all_decors_b64
    delete_decor(decor_name)
    return jsonify({"success": True, "decors": get_all_decors_b64()})


if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")