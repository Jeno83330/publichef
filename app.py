"""
app.py — Interface web PubliChef V2 (Version Production Finale — Envoi Réel Meta & Décors Unifiés)
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

# Récupération du Token Meta stocké dans les variables d'environnement sur Render
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

# Coordonnées officielles du restaurant pour insertion automatique
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

    # 1. Traitement et conversion de la photo du plat
    dish_file.stream.seek(0)
    with open(str(dish_raw), "wb") as f:
        f.write(dish_file.stream.read())
    convert_to_jpg(dish_raw, dish_jpg)

    # 2. Gestion unifiée du fond (Décor permanent ou upload direct)
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
        
        # Sauvegarde physique locale du dernier rendu pour l'envoi API binaire
        last_output = UPLOAD_FOLDER / "last_output.jpg"
        with open(str(last_output), "wb") as f:
            f.write(compressed)
            
        del compressed
        description = ai.describe_dish_from_bytes(img_b64)
        instagram = ai.generate_instagram_caption(description)
        facebook = ai.generate_facebook_caption(description)
        
        # Insertion du bloc de réservation pour le texte affiché sur l'application
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

    # Sécurité : Vérification de l'activation du canal
    if not share_fb:
        return jsonify({"success": False, "error": "La case Facebook est décochée dans vos réglages ⚙️."}), 400

    # Sécurité : Vérification de la présence du Token d'accès Meta
    if not META_ACCESS_TOKEN or META_ACCESS_TOKEN == "":
        return jsonify({"success": False, "error": "Le jeton META_ACCESS_TOKEN n'est pas configuré sur Render."}), 400

    try:
        print("[META API] Envoi réel du média vers le fil Facebook...")
        image_path = UPLOAD_FOLDER / "last_output.jpg"
        if not image_path.exists():
            return jsonify({"success": False, "error": "Fichier image introuvable pour la publication."}), 400

        # Sécurité texte : Injecte le numéro si l'utilisateur l'a effacé par mégarde lors de l'édition
        if PHONE_RESERVATION not in caption_fb:
            caption_fb = f"{caption_fb}\n\n📞 Réservation : {PHONE_RESERVATION}"

        # Requête binaire directe à l'API Graph Meta
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
            return jsonify({"success": False, "error": res_data["error"].get("message", "Erreur Meta API")}), 400
            
        print(f"[META API] Publication en ligne réussie ! ID Post : {res_data.get('id')}")
        return jsonify({"success": True, "fb_post_id": res_data.get('id')})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Synchronisation directe des images décors en Base64 sans modules tiers
@app.route("/get_decors")
def get_decors():
    decors_b64 = {}
    for name in ["salle", "terrasse"]:
        p = UPLOAD_FOLDER / f"decor_{name}.jpg"
        if p.exists():
            with open(p, "rb") as f:
                decors_b64[name] = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        else:
            decors_b64[name] = ""
    return jsonify(decors_b64)


@app.route("/save_decor/<decor_name>", methods=["POST"])
def save_decor_route(decor_name):
    if "image" not in request.files:
        return jsonify({"error": "Aucune image reçue"}), 400
    file = request.files["image"]
    raw_path = UPLOAD_FOLDER / f"decor_{decor_name}_raw"
    jpg_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    
    file.stream.seek(0)
    with open(str(raw_path), "wb") as f:
        f.write(file.stream.read())
        
    convert_to_jpg(raw_path, jpg_path)
    return sync_decors_response()


@app.route("/delete_decor/<decor_name>", methods=["DELETE"])
def delete_decor_route(decor_name):
    p = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    if p.exists():
        p.unlink()
    return sync_decors_response()


def sync_decors_response():
    decors_b64 = {}
    for name in ["salle", "terrasse"]:
        p = UPLOAD_FOLDER / f"decor_{name}.jpg"
        if p.exists():
            with open(p, "rb") as f:
                decors_b64[name] = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        else:
            decors_b64[name] = ""
    return jsonify({"success": True, "decors": decors_b64})


if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")