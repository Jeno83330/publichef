"""
app.py — Interface web PubliChef V2 (Version Production Finale — Sublimation Culinaire Active V2)
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
from PIL import Image, ImageEnhance, ImageOps

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Récupération du Token Meta stocké dans les variables d'environnement sur Render
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

# Coordonnées officielles du restaurant pour insertion automatique
PHONE_RESERVATION = "04 42 08 65 28"

class AdvancedFoodEnhancer:
    """Moteur Culinaire Actif pour sublimer la photo de plat avant intégration."""
    
    @staticmethod
    def enhance_culinary(image_input, image_output):
        try:
            with Image.open(str(image_input)) as im:
                if im.mode != "RGB":
                    im = im.convert("RGB")
                
                # --- Étape 1 : Raviver les couleurs (Saturation Culinaire active) ---
                # On augmente la saturation de 40% pour faire ressortir les couleurs des aliments
                enhancer_sat = ImageEnhance.Color(im)
                im = enhancer_sat.enhance(1.4)
                
                # --- Étape 2 : Le Croustillant (Contraste local & Relief) ---
                # On applique une légère augmentation de contraste pour donner du volume
                enhancer_con = ImageEnhance.Contrast(im)
                im = enhancer_con.enhance(1.2)
                
                # --- Étape 3 : La Brillance (Contrôle de la luminosité et des tons) ---
                # On égalise légèrement pour déboucher les ombres, puis on rehausse la luminosité
                im = ImageOps.autocontrast(im, cutoff=0.5)
                enhancer_bri = ImageEnhance.Brightness(im)
                im = enhancer_bri.enhance(1.1)
                
                # --- Étape 4 : La Netteté Finale ---
                # Légère augmentation de la netteté pour les micro-détails
                enhancer_sha = ImageEnhance.Sharpness(im)
                im = enhancer_sha.enhance(1.3)
                
                # Sauvegarde en haute qualité avant détourage
                im.save(str(image_output), "JPEG", quality=95)
                return True
        except Exception as e:
            print(f"[ERROR CULINARY ENHANCER] : {str(e)}")
            shutil.copy(str(image_input), str(image_output))
            return False

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
    dish_jpg = UPLOAD_FOLDER / "dish.jpg"
    dish_enhanced_jpg = UPLOAD_FOLDER / "dish_enhanced.jpg" 
    env_jpg = UPLOAD_FOLDER / "env.jpg"

    # 1. Traitement et conversion de la photo du plat
    dish_file.stream.seek(0)
    with open(str(dish_raw), "wb") as f:
        f.write(dish_file.stream.read())
    convert_to_jpg(dish_raw, dish_jpg)

    # SUBLIMATION CULINAIRE ACTIVE
    AdvancedFoodEnhancer.enhance_culinary(dish_jpg, dish_enhanced_jpg)

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
        from gemini_engine import GeminiEngine
        from ai_engine import AIEngine

        # Utilisation de la photo sublimée pour l'intégration
        gemini = GeminiEngine()
        composed_path = gemini.compose_dish_in_environment(
            dish_enhanced_jpg, 
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
    share_ig = data.get("instagram", False)
    caption_fb = data.get("caption_fb", "")
    caption_ig = data.get("caption_ig", "")

    if not share_fb and not share_ig:
        return jsonify({"success": False, "error": "Aucun réseau social sélectionné."}), 400

    if not META_ACCESS_TOKEN:
        return jsonify({"success": False, "error": "Le jeton META_ACCESS_TOKEN n'est pas configuré sur Render."}), 400

    image_path = UPLOAD_FOLDER / "last_output.jpg"
    if not image_path.exists():
        return jsonify({"success": False, "error": "Fichier image introuvable pour la publication."}), 400

    fb_success = False
    ig_success = False
    error_msg = []

    # --- 1. SÉCURISATION ET RÉCUPÉRATION DES COMPTES PRO ---
    try:
        page_url = f"https://graph.facebook.com/v25.0/me/accounts"
        page_res = requests.get(page_url, params={'access_token': META_ACCESS_TOKEN}).json()
        
        page_id = None
        instagram_business_id = None

        if "data" in page_res and len(page_res["data"]) > 0:
            page_id = page_res["data"][0].get("id")
            # Requête pour trouver le compte Instagram Business rattaché à cette page Facebook
            ig_url = f"https://graph.facebook.com/v25.0/{page_id}"
            ig_res = requests.get(ig_url, params={'fields': 'instagram_business_account', 'access_token': META_ACCESS_TOKEN}).json()
            if "instagram_business_account" in ig_res:
                instagram_business_id = ig_res["instagram_business_account"].get("id")
    except Exception as e:
        print(f"[META API INFO] Échec récupération ID dynamiques : {e}")

    if not page_id:
        page_id = "me"

    # --- 2. ENVOI SUR FACEBOOK ---
    if share_fb:
        try:
            print(f"[META API] Publication sur la page Facebook {page_id}...")
            if PHONE_RESERVATION not in caption_fb:
                caption_fb = f"{caption_fb}\n\n📞 Réservation : {PHONE_RESERVATION}"

            fb_endpoint = f"https://graph.facebook.com/v25.0/{page_id}/photos"
            payload_fb = {'message': caption_fb, 'access_token': META_ACCESS_TOKEN}
            
            with open(str(image_path), 'rb') as img_file:
                files = {'source': ('post.jpg', img_file, 'image/jpeg')}
                res_fb = requests.post(fb_endpoint, data=payload_fb, files=files).json()

            if "error" in res_fb:
                error_msg.append(f"Facebook: {res_fb['error'].get('message')}")
            else:
                fb_success = True
                print("[META API] Succès Facebook")
        except Exception as e:
            error_msg.append(f"Facebook Exception: {str(e)}")

    # --- 3. ENVOI SUR INSTAGRAM ---
    if share_ig:
        if not instagram_business_id:
            error_msg.append("Instagram: Aucun compte pro associé trouvé sur cette page Facebook.")
        else:
            try:
                print(f"[META API] Début processus Instagram (Compte ID: {instagram_business_id})...")
                
                # Étape A : Créer le conteneur de média (Upload de l'image) via formulaire multipart
                container_url = f"https://graph.facebook.com/v25.0/{instagram_business_id}/media"
                payload_ig = {
                    'caption': caption_ig,
                    'access_token': META_ACCESS_TOKEN
                }
                
                with open(str(image_path), 'rb') as img_file:
                    files_ig = {'image_file': ('post.jpg', img_file, 'image/jpeg')}
                    res_container = requests.post(container_url, data=payload_ig, files=files_ig).json()

                if "error" in res_container:
                    error_msg.append(f"Instagram (Conteneur): {res_container['error'].get('message')}")
                else:
                    creation_id = res_container.get("id")
                    print(f"[META API] Conteneur Instagram créé. ID: {creation_id}. Publication...")

                    # Étape B : Valider et publier le conteneur sur le fil Instagram
                    publish_url = f"https://graph.facebook.com/v25.0/{instagram_business_id}/media_publish"
                    res_publish = requests.post(publish_url, data={
                        'creation_id': creation_id,
                        'access_token': META_ACCESS_TOKEN
                    }).json()

                    if "error" in res_publish:
                        error_msg.append(f"Instagram (Publication): {res_publish['error'].get('message')}")
                    else:
                        ig_success = True
                        print("[META API] Succès Instagram")
            except Exception as e:
                error_msg.append(f"Instagram Exception: {str(e)}")

    # --- 4. BILAN DE LA PUBLICATION ---
    if (share_fb and not fb_success) or (share_ig and not ig_success):
        return jsonify({"success": False, "error": " | ".join(error_msg)}), 500

    return jsonify({"success": True, "message": "Publication validée avec succès !"})


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


# --- INTERFACE DE CONNEXION SÉCURISÉE DE SECOURS ---
@app.route("/connect_meta_auto")
def connect_meta_auto():
    # Modification de l'URI de redirection pour correspondre exactement au domaine autorisé sur Meta
    meta_url = (
        "https://www.facebook.com/v25.0/dialog/oauth"
        "?client_id=1307525461448166"
        "&redirect_uri=https://publichef.onrender.com/connect_meta_auto"
        "&response_type=token"
        "&scope=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,pages_manage_posts"
    )
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Configuration Réseaux PubliChef</title>
        <meta charset="utf-8">
    </head>
    <body style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align:center; padding-top:120px; background-color:#121212; color:#ffffff;">
        <div style="max-width:500px; margin:0 auto; padding:40px 30px; background:#1e1e1e; border-radius:12px; box-shadow: 0 4px 20px rgba(0,0,0,0.6);">
            <h2 style="margin-bottom:15px;">🔑 Liaison PubliChef Pro</h2>
            <p style="color:#aaa; font-size:14px; line-height:1.6; margin-bottom:35px;">
                Cliquez sur le bouton ci-dessous pour déclencher l'ouverture de la fenêtre sécurisée Meta et lier vos profils professionnels.
            </p>
            <a href="{meta_url}" style="display:inline-block; background-color:#0084ff; color:#ffffff; padding:16px 36px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:16px;">
                🔵 SE CONNECTER AVEC FACEBOOK
            </a>
        </div>
    </body>
    </html>
    '''


if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")