"""
app.py — Interface web PubliChef V2 (Version Test Intégration Directe)
"""

import os
import io
import base64
import shutil
import traceback
import gc
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)


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


@app.route("/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        return jsonify({"error": "Aucune image reçue"}), 400

    file = request.files["image"]
    input_path = UPLOAD_FOLDER / "input_raw"
    jpg_path = UPLOAD_FOLDER / "input.jpg"
    file.save(str(input_path))

    try:
        convert_to_jpg(input_path, jpg_path)

        from ai_engine import AIEngine
        from image_processor import ImageProcessor

        processor = ImageProcessor()
        enhanced_path = processor.enhance(jpg_path)
        del processor
        gc.collect()

        with Image.open(enhanced_path) as img:
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
        del compressed
        description = ai.describe_dish_from_bytes(img_b64)
        instagram = ai.generate_instagram_caption(description)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)
        del ai
        gc.collect()

        from history_manager import save_post
        save_post(enhanced_path, description, instagram, facebook, hashtags)

        return jsonify({
            "success": True,
            "description": description,
            "instagram": instagram,
            "facebook": facebook,
            "hashtags": hashtags,
            "image": f"data:image/jpeg;base64,{img_b64}"
        })

    except Exception as e:
        gc.collect()
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/generate_v2", methods=["POST"])
def generate_v2():
    if "dish" not in request.files or "environment" not in request.files:
        return jsonify({"error": "Les deux photos sont requises"}), 400

    dish_file = request.files["dish"]
    env_file = request.files["environment"]

    dish_raw = UPLOAD_FOLDER / "dish_raw"
    env_raw = UPLOAD_FOLDER / "env_raw"
    dish_jpg = UPLOAD_FOLDER / "dish.jpg"
    env_jpg = UPLOAD_FOLDER / "env.jpg"

    dish_file.stream.seek(0)
    with open(str(dish_raw), "wb") as f:
        f.write(dish_file.stream.read())

    env_file.stream.seek(0)
    with open(str(env_raw), "wb") as f:
        f.write(env_file.stream.read())

    convert_to_jpg(dish_raw, dish_jpg)
    convert_to_jpg(env_raw, env_jpg)

    try:
        from image_processor import ImageProcessor
        from gemini_engine import GeminiEngine
        from ai_engine import AIEngine

        processor = ImageProcessor()
        enhanced_dish = processor.enhance(dish_jpg)
        del processor
        gc.collect()

        # TEST : On commente le détourage de Clipdrop pour envoyer l'image brute à Gemini
        # from clipdrop_engine import ClipdropEngine
        # clipdrop = ClipdropEngine()
        # detoured_path = clipdrop.remove_background(enhanced_dish)
        # del clipdrop
        # gc.collect()

        gemini = GeminiEngine()
        # On passe directement 'enhanced_dish' au lieu de 'detoured_path'
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
        del compressed
        description = ai.describe_dish_from_bytes(img_b64)
        instagram = ai.generate_instagram_caption(description)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)
        del ai
        gc.collect()

        from history_manager import save_post
        save_post(composed_path, description, instagram, facebook, hashtags)

        return jsonify({
            "success": True,
            "description": description,
            "instagram": instagram,
            "facebook": facebook,
            "hashtags": hashtags,
            "image": f"data:image/jpeg;base64,{img_b64}"
        })

    except Exception as e:
        gc.collect()
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


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
    print("\nPubliChef V2 - Interface Web")
    print("=" * 40)
    print("Ouvre ton navigateur sur :")
    print("   http://127.0.0.1:5000")
    print("=" * 40 + "\n")
    app.run(debug=False, port=5000, host="0.0.0.0")