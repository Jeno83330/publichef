"""
PubliChef Social Media Agent
Agent d'automatisation Instagram & Facebook pour @athelia_resto
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from ai_engine import AIEngine
from meta_api import MetaAPI
from image_processor import ImageProcessor


def run_agent(image_path: str, dry_run: bool = False):
    """Pipeline principal de l'agent."""
    
    print("\n🍽️  PubliChef Social Media Agent — @athelia_resto")
    print("=" * 55)
    
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"❌ Image introuvable : {image_path}")
        sys.exit(1)
    
    print(f"\n📸 Image source : {image_path.name}")
    
    print("\n🔧 Amélioration de l'image...")
    processor = ImageProcessor()
    enhanced_path = processor.enhance(image_path)
    print(f"   ✅ Image améliorée → {enhanced_path.name}")
    
    print("\n🤖 Analyse IA du plat...")
    ai = AIEngine()
    
    description = ai.describe_dish(enhanced_path)
    print(f"   📝 Description : {description[:80]}...")
    
    print("\n✍️  Rédaction des légendes...")
    instagram_caption = ai.generate_instagram_caption(description)
    facebook_caption = ai.generate_facebook_caption(description)
    hashtags = ai.generate_hashtags(description)
    
    print("\n" + "=" * 55)
    print("📱 LÉGENDE INSTAGRAM")
    print("-" * 55)
    print(instagram_caption)
    print("\n🏷️  Hashtags :", hashtags)
    
    print("\n" + "=" * 55)
    print("👥 LÉGENDE FACEBOOK")
    print("-" * 55)
    print(facebook_caption)
    
    if dry_run:
        print("\n\n⚠️  MODE TEST — Publication simulée (--dry-run activé)")
        return
    
    full_ig_text = f"{instagram_caption}\n\n{hashtags}"
    full_fb_text = facebook_caption
    
    print("\n\n🚀 Publication en cours...")
    meta = MetaAPI()
    
    ig_result = meta.publish_instagram(str(enhanced_path), full_ig_text)
    fb_result = meta.publish_facebook(str(enhanced_path), full_fb_text)
    
    if ig_result:
        print(f"   ✅ Instagram publié  (ID : {ig_result})")
    else:
        print("   ❌ Échec publication Instagram")
    
    if fb_result:
        print(f"   ✅ Facebook publié   (ID : {fb_result})")
    else:
        print("   ❌ Échec publication Facebook")
    
    print("\n🎉 Terminé !\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PubliChef — Agent social media pour @athelia_resto"
    )
    parser.add_argument("image", help="Chemin vers la photo du plat")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Génère les textes sans publier (mode test)"
    )
    args = parser.parse_args()
    run_agent(args.image, dry_run=args.dry_run)