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
    # Ton interface cherche "decors" (au pluriel) dans la réponse
    decors_list = ["salle", "terrasse"]
    return jsonify({"decors": decors_list})

@app.route("/generate_v2", methods=["POST"])
def generate_v2():
    # ICI LE RACCORDEMENT : Ton interface envoie 'dish_image' et 'decor_type'
    if "dish_image" not in request.files:
        return jsonify({"error": "Photo manquante (dish_image)"}), 400

    dish_file = request.files["dish_image"]
    decor_name = request.form.get("decor_type", "salle")

    dish_raw = UPLOAD_FOLDER / "dish_raw"
    dish_enhanced_jpg = UPLOAD_FOLDER / "dish_enhanced.jpg"
    dish_hq_jpg = UPLOAD_FOLDER / "dish_hq.jpg"
    env_jpg = UPLOAD_FOLDER / "env.jpg"

    dish_file.stream.seek(0)
    with open(str(dish_raw), "wb") as f:
        f.write(dish_file.stream.read())

    resize_and_convert_to_jpg(dish_raw, dish_enhanced_jpg, max_size=(900, 900))
    resize_and_convert_to_jpg(dish_raw, dish_hq_jpg, max_size=(1200, 1200))

    saved_decor_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    if saved_decor_path.exists():
        shutil.copy(str(saved_decor_path), str(env_jpg))
    else:
        return jsonify({"error": "Décor introuvable"}), 400

    try:
        from gemini_engine import GeminiEngine
        from ai_engine import AIEngine

        gemini = GeminiEngine()
        composed_path = gemini.compose_dish_in_environment(dish_enhanced_jpg, env_jpg)
        
        with open(composed_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Ton interface cherche 'image_url' et 'caption'
        image_url_data = f"data:image/jpeg;base64,{img_b64}"

        with open(str(dish_hq_jpg), "rb") as f_hq:
            dish_hq_b64 = base64.b64encode(f_hq.read()).decode("utf-8")

        ai = AIEngine()
        description = ai.describe_dish_from_bytes(dish_hq_b64)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)
        
        caption_final = f"{facebook}\n\n📞 Réservation : {PHONE_RESERVATION}\n\n{hashtags}"

        return jsonify({
            "success": True,
            "image_url": image_url_data,
            "caption": caption_final
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/save_decor/<decor_name>", methods=["POST"])
def save_decor_route(decor_name):
    if "image" not in request.files: return jsonify({"error": "No image"}), 400
    file = request.files["image"]
    jpg_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    file.save(str(jpg_path))
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
