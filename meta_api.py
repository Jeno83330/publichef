"""
meta_api.py — Connexion à la Meta Graph API
Publication sur Instagram (@athelia_resto) et Facebook Page Athelia
"""

import os
import base64
import requests


class MetaAPI:

    GRAPH_VERSION = "v19.0"
    GRAPH_BASE    = "https://graph.facebook.com/v19.0"

    def __init__(self):
        self.ig_user_id   = os.getenv("META_IG_USER_ID")
        self.fb_page_id   = os.getenv("META_FB_PAGE_ID")
        self.access_token = os.getenv("META_ACCESS_TOKEN")

        missing = []
        if not self.ig_user_id:   missing.append("META_IG_USER_ID")
        if not self.fb_page_id:   missing.append("META_FB_PAGE_ID")
        if not self.access_token: missing.append("META_ACCESS_TOKEN")

        if missing:
            raise EnvironmentError(
                f"❌ Variables manquantes dans .env : {', '.join(missing)}"
            )

    def publish_instagram(self, image_path: str, caption: str) -> object:
        image_url = self._get_public_url(image_path)
        if not image_url:
            print("   ⚠️  Impossible d'obtenir une URL publique pour Instagram.")
            return None

        container_url = f"{self.GRAPH_BASE}/{self.ig_user_id}/media"
        r = requests.post(container_url, data={
            "image_url":    image_url,
            "caption":      caption,
            "access_token": self.access_token,
        }, timeout=30)

        if not r.ok:
            print(f"   ❌ Erreur création container IG : {r.json()}")
            return None

        container_id = r.json().get("id")

        r2 = requests.post(
            f"{self.GRAPH_BASE}/{self.ig_user_id}/media_publish",
            data={
                "creation_id":  container_id,
                "access_token": self.access_token,
            },
            timeout=30,
        )

        if not r2.ok:
            print(f"   ❌ Erreur publication IG : {r2.json()}")
            return None

        return r2.json().get("id")

    def publish_facebook(self, image_path: str, message: str) -> object:
        url = f"{self.GRAPH_BASE}/{self.fb_page_id}/photos"

        with open(image_path, "rb") as img_file:
            r = requests.post(url, data={
                "message":      message,
                "access_token": self.access_token,
            }, files={"source": img_file}, timeout=60)

        if not r.ok:
            print(f"   ❌ Erreur publication FB : {r.json()}")
            return None

        return r.json().get("post_id") or r.json().get("id")

    def _get_public_url(self, image_path: str) -> object:
        imgbb_key = os.getenv("IMGBB_API_KEY")
        if not imgbb_key:
            print("   ℹ️  IMGBB_API_KEY non configurée.")
            return None

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": imgbb_key, "image": image_b64, "expiration": 600},
            timeout=30,
        )

        if r.ok:
            return r.json()["data"]["url"]

        print(f"   ❌ Échec upload imgbb : {r.json()}")
        return None

    def verify_token(self) -> bool:
        r = requests.get(
            f"{self.GRAPH_BASE}/me",
            params={"access_token": self.access_token},
            timeout=10,
        )
        if r.ok:
            print(f"   ✅ Token valide — Compte : {r.json().get('name', 'inconnu')}")
            return True
        print(f"   ❌ Token invalide : {r.json().get('error', {}).get('message')}")
        return False