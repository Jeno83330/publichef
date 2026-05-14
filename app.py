"""
app.py — Interface web PubliChef V2
"""

import os
import io
import base64
import shutil
import subprocess
import traceback
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)


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
        subprocess.run(
            ["sips", "-s", "format", "jpeg", str(input_path), "--out", str(jpg_path)],
            capture_output=True
        )
        if not jpg_path.exists():
            shutil.copy(str(input_path), str(jpg_path))

        from ai_engine import AIEngine
        from image_processor import ImageProcessor

        processor = ImageProcessor()
        enhanced_path = processor.enhance(jpg_path)

        with Image.open(enhanced_path) as img:
            quality = 85
            while True:
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=quality)
                if len(buffer.getvalue()) <= 4 * 1024 * 1024 or quality < 30:
                    break
                quality -= 10
            compressed = buffer.getvalue()

        ai = AIEngine()
        img_b64 = base64.b64encode(compressed).decode("utf-8")
        description = ai.describe_dish_from_bytes(img_b64)
        instagram = ai.generate_instagram_caption(description)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)

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

    for src, dst in [(dish_raw, dish_jpg), (env_raw, env_jpg)]:
        subprocess.run(
            ["sips", "-s", "format", "jpeg", str(src), "--out", str(dst)],
            capture_output=True
        )
        if not dst.exists():
            shutil.copy(str(src), str(dst))

    try:
        from image_processor import ImageProcessor
        from clipdrop_engine import ClipdropEngine
        from gemini_engine import GeminiEngine
        from ai_engine import AIEngine

        processor = ImageProcessor()
        enhanced_dish = processor.enhance(dish_jpg)

        clipdrop = ClipdropEngine()
        detoured_path = clipdrop.remove_background(enhanced_dish)

        gemini = GeminiEngine()
        composed_path = gemini.compose_dish_in_environment(
            detoured_path,
            env_jpg
        )

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

        ai = AIEngine()
        img_b64 = base64.b64encode(compressed).decode("utf-8")
        description = ai.describe_dish_from_bytes(img_b64)
        instagram = ai.generate_instagram_caption(description)
        facebook = ai.generate_facebook_caption(description)
        hashtags = ai.generate_hashtags(description)

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
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


if __name__ == "__main__":
    print("\n🍽️  PubliChef V2 — Interface Web")
    print("=" * 40)
    print("✅ Ouvre ton navigateur sur :")
    print("   http://127.0.0.1:5000")
    print("=" * 40 + "\n")
    app.run(debug=True, port=5000, host="0.0.0.0")