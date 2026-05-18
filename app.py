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
    target_file_key = None
    for key in request.files.keys():
        target_file_key = key
        break
    if not target_file_key:
        return jsonify({"error": "Fichier manquant"}), 400
    try:
        file = request.files[target_file_key]
        raw_path = UPLOAD_FOLDER / f"decor_{decor_name}_raw"
        jpg_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
        file.save(str(raw_path))
        resize_and_convert_to_jpg(raw_path, jpg_path, max_size=(1200, 1200))
        with open(jpg_path, "rb") as f:
            new_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        return jsonify({"success": True, "decor_type": decor_name, "image_b64": new_b64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_v2", methods=["POST"])
def generate_v2():
    if "dish" not in request.files:
        return jsonify({"error": "Photo du plat manquante dans la requete."}), 400
    dish_file_key = "dish"

    decor_name = request.form.get("decor", request.form.get("decor_type", "salle"))
    dish_raw = UPLOAD_FOLDER / "dish_raw"
    dish_jpg = UPLOAD_FOLDER / "dish.jpg"
    dish_hq_jpg = UPLOAD_FOLDER / "dish_hq.jpg"
    env_jpg = UPLOAD_FOLDER / "env.jpg"

    try:
        request.files[dish_file_key].save(str(dish_raw))
        resize_and_convert_to_jpg(dish_raw, dish_jpg, max_size=(900, 900))
        resize_and_convert_to_jpg(dish_raw, dish_hq_jpg, max_size=(1400, 1400))
    except Exception as e:
        return jsonify({"error": f"Erreur traitement image plat: {str(e)}"}), 200

    if "environment" in request.files and request.files["environment"].filename != '':
        try:
            env_raw = UPLOAD_FOLDER / "env_raw"
            request.files["environment"].save(str(env_raw))
            resize_and_convert_to_jpg(env_raw, env_jpg, max_size=(1024, 1024))
        except Exception:
            saved_decor_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
            if saved_decor_path.exists(): shutil.copy(str(saved_decor_path), str(env_jpg))
    else:
        saved_decor_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
        if saved_decor_path.exists():
            shutil.copy(str(saved_decor_path), str(env_jpg))
        else:
            default_path = UPLOAD_FOLDER / "decor_salle.jpg"
            if default_path.exists():
                shutil.copy(str(default_path), str(env_jpg))
            else:
                return jsonify({"error": "Aucun decor permanent trouve en base. Re-ajoutez votre salle."}), 200

    # Capture d'erreur precise renvoyee directement au format lisible
    try:
        gc.collect()
        from gemini_engine import GeminiEngine
        from ai_engine import AIEngine

        gemini = GeminiEngine()
        composed_path = gemini.compose_dish_in_environment(dish_jpg, env_jpg)
        del gemini
        gc.collect()

        with Image.open(composed_path) as img:
            if img.mode != "RGB": img = img.convert("RGB")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        composed_url = f"data:image/jpeg;base64,{img_b64}"

        with open(str(dish_hq_jpg), "rb") as f_hq:
            dish_hq_b64 = base64.b64encode(f_hq.read()).decode("utf-8")

        ai = AIEngine()
        description = ai.describe_dish_from_bytes(dish_hq_b64)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)
        del ai
        gc.collect()

        facebook_final = f"{facebook.strip()}\n\n📞 Reservation : {PHONE_RESERVATION}\n\n{hashtags}"

        return jsonify({
            "success": True,
            "image": composed_url,
            "facebook": facebook_final
        })

    except Exception as e:
        # On change le code de retour en 200 pour forcer l'affichage de la vraie erreur Python a l'ecran !
        return jsonify({"error": f"Erreur de l'IA (Verifiez vos cles API) : {str(e)}"}), 200

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
