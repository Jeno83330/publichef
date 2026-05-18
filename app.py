import os
import io
import base64
import shutil
import traceback
import gc
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from PIL import Image, ImageEnhance, ImageOps

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_RESERVATION = "04 42 08 65 28"

def resize_and_convert_to_jpg(src, dst, max_size=(900, 900)):
    try:
        with Image.open(str(src)) as im:
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.thumbnail(max_size, Image.Resampling.LANCZOS)
            im.save(str(dst), "JPEG", quality=82)
    except Exception:
        shutil.copy(str(src), str(dst))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_decor_secours", methods=["GET", "POST"])
def upload_decor_secours():
    if request.method == "POST":
        if "decor_file" not in request.files:
            return "<h3>Erreur : Aucun fichier détecté dans la requête.</h3>", 400
        file = request.files["decor_file"]
        decor_name = request.form.get("decor_name", "salle")
        if file.filename == "":
            return "<h3>Erreur : Le fichier sélectionné est vide.</h3>", 400
            
        raw_path = UPLOAD_FOLDER / f"decor_{decor_name}_raw"
        jpg_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
        
        file.save(str(raw_path))
        resize_and_convert_to_jpg(raw_path, jpg_path, max_size=(1000, 1000))
        return f"<h3>Succes ! Le decor '{decor_name}' a ete enregistre de force sur Render.</h3><a href='/'>Retour a l'accueil</a>"

    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Secours PubliChef</title><meta charset="utf-8"></head>
    <body style="font-family:sans-serif; background:#121212; color:#fff; padding:50px; text-align:center;">
        <div style="max-width:500px; margin:0 auto; background:#1e1e1e; padding:30px; border-radius:10px; border:1px solid #333;">
            <h2>🛠️ Passerelle de Secours Décors</h2>
            <form action="/upload_decor_secours" method="post" enctype="multipart/form-data" style="margin-top:30px;">
                <label>1. Emplacement cible :</label><br>
                <select name="decor_name" style="padding:10px; width:100%; margin:10px 0; background:#222; color:#fff; border:1px solid #444;">
                    <option value="salle">Salle</option>
                    <option value="terrasse">Terrasse</option>
                </select><br><br>
                <label>2. Fichier JPEG sur le Mac :</label><br>
                <input type="file" name="decor_file" accept="image/*" style="margin:20px 0;"><br><br>
                <input type="submit" value="FORCER L'INSTALLATION" style="background:#d4af37; color:#000; padding:12px 25px; border:none; font-weight:bold; cursor:pointer; width:100%;">
            </form>
        </div>
    </body>
    </html>
    '''

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
    return jsonify({"success": True, "decors": decors_b64})

@app.route("/save_decor/<decor_name>", methods=["POST"])
def save_decor_route(decor_name):
    file_key = None
    for key in request.files.keys():
        file_key = key
        break
    if not file_key and "image" in request.files:
        file_key = "image"
    if not file_key:
        return jsonify({"error": "Fichier manquant"}), 400
    try:
        file = request.files[file_key]
        raw_path = UPLOAD_FOLDER / f"decor_{decor_name}_raw"
        jpg_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
        file.stream.seek(0)
        with open(str(raw_path), "wb") as f:
            f.write(file.stream.read())
        resize_and_convert_to_jpg(raw_path, jpg_path, max_size=(1000, 1000))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_v2", methods=["POST"])
def generate_v2():
    target_file_key = "dish_image" if "dish_image" in request.files else "dish"
    target_decor_key = "decor_type" if "decor_type" in request.form else "decor"

    if target_file_key not in request.files:
        return jsonify({"error": "La photo du plat est requise"}), 400

    dish_file = request.files[target_file_key]
    decor_name = request.form.get(target_decor_key, "salle")

    dish_raw = UPLOAD_FOLDER / "dish_raw"
    dish_jpg = UPLOAD_FOLDER / "dish.jpg"
    dish_enhanced_jpg = UPLOAD_FOLDER / "dish_enhanced.jpg"
    dish_hq_jpg = UPLOAD_FOLDER / "dish_hq.jpg"
    env_jpg = UPLOAD_FOLDER / "env.jpg"

    dish_file.stream.seek(0)
    with open(str(dish_raw), "wb") as f:
        f.write(dish_file.stream.read())

    resize_and_convert_to_jpg(dish_raw, dish_jpg, max_size=(900, 900))
    resize_and_convert_to_jpg(dish_raw, dish_hq_jpg, max_size=(1200, 1200))
    gc.collect()

    try:
        with Image.open(str(dish_jpg)) as im:
            if im.mode != "RGB": im = im.convert("RGB")
            im = ImageEnhance.Color(im).enhance(1.25)
            im = ImageEnhance.Contrast(im).enhance(1.20)
            im = ImageOps.autocontrast(im, cutoff=0.5)
            im = ImageEnhance.Brightness(im).enhance(1.08)
            im = ImageEnhance.Sharpness(im).enhance(1.30)
            im.save(str(dish_enhanced_jpg), "JPEG", quality=88)
    except Exception:
        shutil.copy(str(dish_jpg), str(dish_enhanced_jpg))

    saved_decor_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    if "environment" in request.files and request.files["environment"].filename != '':
        env_file = request.files["environment"]
        env_raw = UPLOAD_FOLDER / "env_raw"
        env_file.stream.seek(0)
        with open(str(env_raw), "wb") as f:
            f.write(env_file.stream.read())
        resize_and_convert_to_jpg(env_raw, env_jpg, max_size=(900, 900))
    elif saved_decor_path.exists():
        shutil.copy(str(saved_decor_path), str(env_jpg))
    else:
        return jsonify({"error": f"Aucun décor trouvé pour '{decor_name}'."}), 400

    try:
        from gemini_engine import GeminiEngine
        from ai_engine import AIEngine

        gemini = GeminiEngine()
        composed_path = gemini.compose_dish_in_environment(dish_enhanced_jpg, env_jpg)
        del gemini
        gc.collect()

        with Image.open(composed_path) as img:
            if img.mode != "RGB": img = img.convert("RGB")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            compressed = buffer.getvalue()

        img_b64 = base64.b64encode(compressed).decode("utf-8")
        image_url_data = f"data:image/jpeg;base64,{img_b64}"

        with open(str(dish_hq_jpg), "rb") as f_hq:
            dish_hq_b64 = base64.b64encode(f_hq.read()).decode("utf-8")

        ai = AIEngine()
        description = ai.describe_dish_from_bytes(dish_hq_b64)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)
        del ai
        gc.collect()

        facebook_final = f"{facebook.strip()}\n\n📞 Réservation : {PHONE_RESERVATION}\n\n{hashtags}"

        return jsonify({
            "success": True,
            "caption": facebook_final,
            "hashtags": hashtags,
            "image_url": image_url_data,
            "image": image_url_data
        })

    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
