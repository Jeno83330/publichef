"""
ai_engine.py — Moteur IA : vision + génération de textes
"""

import os
import base64
import anthropic
from pathlib import Path


SYSTEM_PROMPT = """Tu es le rédacteur social media du restaurant Athelia, à La Ciotat (Var).
Tu écris comme un restaurateur passionné : chaleureux, "vieille école" dans les valeurs
mais moderne dans la forme. Tu mets en avant :
- Les produits frais et locaux (Provence, Var, PACA)
- L'ambiance conviviale et familiale
- Le savoir-faire artisanal et le fait maison
- La générosité et le plaisir de la table

Ton style : phrases courtes, visuelles, appétissantes. Pas de jargon marketing.
Toujours en français."""


class AIEngine:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY manquante dans le fichier .env")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-5"

    def describe_dish(self, image_path: Path) -> str:
        image_data = self._encode_image(image_path)
        media_type = self._get_media_type(image_path)
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Décris ce plat avec précision : ingrédients visibles, couleurs, présentation, texture apparente. Sois factuel et appétissant. 3-4 phrases maximum.",
                        },
                    ],
                }
            ],
        )
        return message.content[0].text

    def describe_dish_from_bytes(self, image_b64: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Décris ce plat avec précision : ingrédients visibles, couleurs, présentation, texture apparente. Sois factuel et appétissant. 3-4 phrases maximum.",
                        },
                    ],
                }
            ],
        )
        return message.content[0].text

    def generate_instagram_caption(self, dish_description: str) -> str:
        prompt = f"""Voici la description d'un plat servi chez Athelia :
"{dish_description}"

Rédige une légende Instagram en français :
- 3 à 5 lignes maximum, rythmée et visuelle
- Commence par une phrase qui donne faim ou crée de l'émotion
- Mentionne @athelia_resto une fois naturellement
- Ton chaleureux et passionné, pas marketing
- Termine par une invitation à venir
- NE PAS inclure les hashtags"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    def generate_facebook_caption(self, dish_description: str) -> str:
        prompt = f"""Voici la description d'un plat servi chez Athelia :
"{dish_description}"

Rédige une publication Facebook en français :
- 5 à 8 lignes, plus développée qu'Instagram
- Raconte l'histoire du plat : origine des produits, technique, saison
- Mentionne les produits locaux (Provence, Var) si pertinent
- Ton convivial et authentique
- Inclure une question pour encourager les commentaires
- Terminer avec : "Réservations : [TELEPHONE]" et "📍 La Ciotat"
- NE PAS inclure les hashtags"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    def generate_hashtags(self, dish_description: str) -> str:
        prompt = f"""Plat décrit : "{dish_description}"

Génère exactement 10 hashtags Instagram pour ce plat.
Mélange obligatoire :
- 2-3 tags locaux : #Var #PACA #LaCiotat #LeBeausset #Provence
- 2-3 tags thématiques cuisine : #faitmaison #cuisinefrancaise etc.
- 2-3 tags restaurant : #restaurant #gastronomie #bonneadresse etc.
- 1-2 tags spécifiques au plat

Format : sur une seule ligne, séparés par des espaces.
Uniquement les hashtags, rien d'autre."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    def _encode_image(self, image_path: Path) -> str:
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    def _get_media_type(self, image_path: Path) -> str:
        ext = image_path.suffix.lower()
        types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return types.get(ext, "image/jpeg")