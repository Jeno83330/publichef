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

class AdvancedFoodEnhancer:
    @staticmethod
    def enhance_culinary(image_input, image_output):
        try:
            with Image.open(str(image_input)) as im:
                if im.mode != "RGB":
                    im = im.convert("RGB")
                im = ImageEnhance.Color(im).enhance(1.25)
                im = ImageEnhance.Contrast(im).enhance(1.20)
                im = ImageOps.autocontrast(im, cutoff=0.5)
                im = ImageEnhance.Brightness(im).enhance(1.08)
                im = ImageEnhance.Sharpness(im).enhance(1.30)
                im.save(str(image_output), "JPEG", quality=88)
                return True
        except Exception as e:
            print(f"[ERROR CULINARY ENHANCER] : {str(e)}")
            shutil.copy(str(image_input), str(image_output))
            return False

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

    try:
        dish_file.stream.seek(0)
        with open(str(dish_raw), "wb") as f:
            f.write(dish_file.stream.read())

        resize_and_convert_to_jpg(dish_raw, dish_jpg, max_size=(900, 900))
        resize_and_convert_to_jpg(dish_raw, dish_hq_jpg, max_size=(1200, 1200))
        gc.collect()

        AdvancedFoodEnhancer.enhance_culinary(dish_jpg, dish_enhanced_jpg)
        gc.collect()

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
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            compressed = buffer.getvalue()

        last_output = UPLOAD_FOLDER / "last_output.jpg"
        with open(str(last_output), "wb") as f:
            f.write(compressed)

        img_b64 = base64.b64encode(compressed).decode("utf-8")
        image_url_data = f"data:image/jpeg;base64,{img_b64}"
        del compressed
        gc.collect()

        with open(str(dish_hq_jpg), "rb") as f_hq:
            dish_hq_b64 = base64.b64encode(f_hq.read()).decode("utf-8")

        ai = AIEngine()
        description = ai.describe_dish_from_bytes(dish_hq_b64)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)
        del ai
        gc.collect()

        facebook_clean = facebook.strip()
        for token in ["[TELEPHONE]", "TELEPHONE", "Réservations :", "Réservation :"]:
            facebook_clean = facebook_clean.replace(token, "").strip()
        facebook_final = f"{facebook_clean}\n\n📞 Réservation : {PHONE_RESERVATION}\n\n{hashtags}"

        try:
            from history_manager import save_post
            save_post(composed_path, description, "", facebook_final, "")
        except Exception:
            pass

        return jsonify({
            "success": True,
            "caption": facebook_final,
            "hashtags": hashtags,
            "image_url": image_url_data
        })

    except Exception as e:
        gc.collect()
        # TECHNIQUE DE DEBUG : On renvoie la ligne exacte de l'erreur dans le champ d'erreur standard
        error_detail = f"Erreur backend : {str(e)} | Emplacement : {traceback.format_exc().splitlines()[-2]}"
        return jsonify({"error": error_detail}), 400

# Le reste des routes secondaires reste inchangé
@app.route("/history_data")
def history_data():
    try:
        from history_manager import get_all_posts
        return jsonify(get_all_posts())
    except Exception: return jsonify([])

@app.route("/delete_post/<post_id>", methods=["DELETE"])
def delete_post(post_id):
    try:
        from history_manager import delete_post as dp
        return jsonify({"success": dp(post_id)})
    except Exception: return jsonify({"success": False})

@app.route("/publish_to_socials", methods=["POST"])
def publish_to_socials():
    return jsonify({"success": False, "error": "Liaison inactive pendant le debug."})

@app.route("/save_decor/<decor_name>", methods=["POST"])
def save_decor_route(decor_name):
    if "image" not in request.files: return jsonify({"error": "Aucune image"}), 400
    file = request.files["image"]
    raw_path = UPLOAD_FOLDER / f"decor_{decor_name}_raw"
    jpg_path = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    file.stream.seek(0)
    with open(str(raw_path), "wb") as f: f.write(file.stream.read())
    resize_and_convert_to_jpg(raw_path, jpg_path, max_size=(1000, 1000))
    return sync_decors_response()

@app.route("/delete_decor/<decor_name>", methods=["DELETE"])
def delete_decor_route(decor_name):
    p = UPLOAD_FOLDER / f"decor_{decor_name}.jpg"
    if p.exists(): p.unlink()
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
    return "Debug actif."

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
