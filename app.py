"""
app.py — Interface web PubliChef V2 (Version Diagnostic Debug)
"""

import os
import io
import base64
import shutil
import traceback
import gc
import requests
import numpy as np
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

def resize_and_convert_to_jpg(src, dst, max_size=(1440, 1440)):
    """Ajuste l'image au format HD optimal pour préserver le piqué sans saturer l'API Meta."""
    try:
        with Image.open(str(src)) as im:
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.thumbnail(max_size, Image.Resampling.LANCZOS)
            im.save(str(dst), "JPEG", quality=92)
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
    dish_jpg = UPLOAD_FOLDER / "dish.jpg"
    dish_enhanced_jpg = UPLOAD_FOLDER / "dish_enhanced.jpg" 
    dish_ai = UPLOAD_FOLDER / "dish_ai.jpg"
    env_jpg = UPLOAD_FOLDER / "env.jpg"

    try:
        dish_file.stream.seek(0)
        with open(str(dish_raw), "wb") as f:
            f.write(dish_file.stream.read())
            
        resize_and_convert_to_jpg(dish_raw, dish_jpg, max_size=(1440, 1440))
        resize_and_convert_to_jpg(dish_raw, dish_ai, max_size=(2000, 2000))

        shutil.copy(str(dish_jpg), str(dish_enhanced_jpg))

        saved_decor_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
        if "environment" in request.files and request.files["environment"].filename != '':
            env_file = request.files["environment"]
            env_raw = UPLOAD_FOLDER / "env_raw"
            env_file.stream.seek(0)
            with open(str(env_raw), "wb") as f:
                f.write(env_file.stream.read())
            resize_and_convert_to_jpg(env_raw, env_jpg, max_size=(1440, 1440))
        elif saved_decor_path.exists():
            shutil.copy(str(saved_decor_path), str(env_jpg))
        else:
            return jsonify({"error": f"Aucun décor trouvé pour '{decor_name}'."}), 400

        from gemini_engine import GeminiEngine
        from ai_engine import AIEngine

        gc.collect()
        gemini = GeminiEngine()
        composed_path = gemini.compose_dish_in_environment(dish_enhanced_jpg, env_jpg)
        del gemini
        gc.collect()

        with Image.open(composed_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail((1440, 1440), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=92)
            compressed = buffer.getvalue()

        last_output = UPLOAD_FOLDER / "last_output.jpg"
        with open(str(last_output), "wb") as f:
            f.write(compressed)
            
        img_b64 = base64.b64encode(compressed).decode("utf-8")
        del compressed
        gc.collect()

        with open(str(dish_ai), "rb") as f_ai:
            dish_raw_b64 = base64.b64encode(f_ai.read()).decode("utf-8")

        ai = AIEngine()
        description = ai.describe_dish_from_bytes(dish_raw_b64)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)
        
        facebook_clean = facebook.replace("[TELEPHONE]", "").replace("TELEPHONE", "").strip()
        facebook_clean = facebook_clean.replace("Réservations :", "").replace("Réservation :", "").strip()
        facebook_final = f"{facebook_clean}\n\n📞 Réservation : {PHONE_RESERVATION}\n\n{hashtags}"
        
        del ai
        gc.collect()

        from history_manager import save_post
        save_post(composed_path, description, "", facebook_final, "")

        return jsonify({
            "success": True,
            "description": description,
            "facebook": facebook_final,
            "image": f"data:image/jpeg;base64,{img_b64}"
        })

    except Exception as e:
        gc.collect()
        # CAPTURE DE FLUX : On force l'application à renvoyer le vrai coupable à l'écran
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/publish_to_socials", methods=["POST"])
def publish_to_socials():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Données invalides"}), 400

    caption_fb = data.get("caption_fb", "")

    if not META_ACCESS_TOKEN:
        return jsonify({"success": False, "error": "Le jeton META_ACCESS_TOKEN n'est pas configuré sur Render."}), 400

    image_path = UPLOAD_FOLDER / "last_output.jpg"
    if not image_path.exists():
        return jsonify({"success": False, "error": "Fichier image introuvable. Veuillez recréer le post."}), 400

    try:
        page_url = f"https://graph.facebook.com/v25.0/me/accounts"
        page_res = requests.get(page_url, params={'access_token': META_ACCESS_TOKEN}).json()
        
        if "error" in page_res:
            return jsonify({"success": False, "error": "Meta Auth: " + page_res["error"].get("message")}), 500

        page_id = page_res["data"][0].get("id") if "data" in page_res and len(page_res["data"]) > 0 else "me"
        
        fb_endpoint = f"https://graph.facebook.com/v25.0/{page_id}/photos"
        payload_fb = {'message': caption_fb, 'access_token': META_ACCESS_TOKEN}
        
        with open(str(image_path), 'rb') as img_file:
            files = {'source': ('post.jpg', img_file, 'image/jpeg')}
            res_fb = requests.post(fb_endpoint, data=payload_fb, files=files).json()

        if "error" in res_fb:
            return jsonify({"success": False, "error": res_fb["error"].get("message")}), 500
            
        return jsonify({"success": True, "message": "Plat publié avec succès !"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
        
    resize_and_convert_to_jpg(raw_path, jpg_path, max_size=(1440, 1440))
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


@app.route("/connect_meta_auto")
def connect_meta_auto():
    meta_url = (
        "https://www.facebook.com/v25.0/dialog/oauth"
        "?client_id=1307525461448166"
        "&redirect_uri=https://publichef.onrender.com/connect_meta_auto"
        "&response_type=token"
        "&scope=pages_show_list,pages_read_engagement,pages_manage_posts,public_profile"
    )
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Configuration Réseaux PubliChef</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family:sans-serif; text-align:center; padding-top:60px; background-color:#0A0A0F; color:#ffffff; padding-inline:20px;">
        <div style="max-width:500px; margin:0 auto; padding:40px 30px; background:#13131A; border: 1px solid rgba(255,255,255,0.08); border-radius:24px;">
            <h2 style="color:#F5C842; margin-bottom:15px;">🔑 Liaison PubliChef Pro</h2>
            <p style="color:#aaa; font-size:14px; margin-bottom:35px; line-height:1.5;">Cliquez sur le bouton bleu. Votre jeton permanent apparaîtra automatiquement ci-dessous.</p>
            
            <a href="{meta_url}" style="display:inline-block; background: linear-gradient(135deg, #0084ff 0%, #0052cc 100%); color:#ffffff; padding:16px 36px; text-decoration:none; border-radius:12px; font-weight:bold; margin-bottom:20px;">🔵 LIER LA PAGE FACEBOOK</a>
            
            <div id="token-display" style="display:none; margin-top:30px; padding:20px; background:rgba(255,255,255,0.04); border-radius:12px; border:1px dashed rgba(245,200,66,0.3);">
                <p style="color:#34C759; font-weight:bold; margin-bottom:10px;">✅ JETON RECONNU AVEC SUCCÈS :</p>
                <textarea id="token-text" readonly style="width:100%; height:120px; background:#000; color:#FFE08A; border:1px solid #333; border-radius:8px; padding:10px; font-family:monospace; font-size:12px; box-sizing:border-box; resize:none;"></textarea>
                <p style="font-size:12px; color:#8E8E93; margin-top:10px;">Copiez ce texte et collez-le dans META_ACCESS_TOKEN sur Render.</p>
            </div>
        </div>

        <script>
            const hash = window.location.hash;
            if (hash) {{
                const params = new URLSearchParams(hash.replace('#', '?'));
                const token = params.get('access_token');
                if (token) {{
                    document.getElementById('token-display').style.display = 'block';
                    document.getElementById('token-text').value = token;
                }}
            }}
        </script>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0") # Mode diagnostic activé