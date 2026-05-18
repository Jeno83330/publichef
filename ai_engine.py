import os
import anthropic

class AIEngine:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY manquante")
        self.client = anthropic.Anthropic(api_key=api_key)

    def describe_dish_from_bytes(self, img_b64):
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":img_b64}},{"type":"text","text":"Decris ce plat en 2-3 phrases pour un restaurateur. Nom du plat, ingredients, presentation. Sois precis et appetissant."}]}]
        )
        return message.content[0].text

    def generate_facebook_caption(self, description):
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role":"user","content":f"Tu es un restaurateur passionne du Var a La Ciotat. Ecris une publication Facebook (max 200 mots) pour ce plat : {description}. Ton chaleureux et authentique. Pas de hashtags. Pas de numero de telephone."}]
        )
        return message.content[0].text

    def generate_hashtags(self, description):
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role":"user","content":f"Genere 10 hashtags pour ce plat de restaurant a La Ciotat dans le Var : {description}. Inclus #LaCiotat #Var #Provence. Format: #tag1 #tag2..."}]
        )
        return message.content[0].text
