from pathlib import Path
from datetime import datetime
import csv
import json
import re
import unicodedata


SITE_URL = "https://marylouse-ofertas.vercel.app"

OFFERS_PATH = Path("data/offers.json")
OUTPUT_DIR = Path("growth/output")


CATEGORY_DEFS = [
    {"label": "Mamãe e Bebê", "category": "Mãe e Bebê", "slug": "mae-bebe", "emoji": "🍼", "channel": "Mamãe e Bebê", "time": "09:00 - 11:00"},
    {"label": "Moda Feminina", "category": "Moda Feminina", "slug": "moda-feminina", "emoji": "👗", "channel": "Moda Feminina", "time": "12:00 - 14:00"},
    {"label": "Casa e Cozinha", "category": "Casa e Cozinha", "slug": "casa-cozinha", "emoji": "🍳", "channel": "Casa e Cozinha", "time": "18:00 - 20:00"},
    {"label": "Celulares e Tecnologia", "category": "Celulares", "slug": "celulares", "emoji": "📱", "channel": "Celulares e Tecnologia", "time": "19:00 - 21:00"},
    {"label": "Beleza e Cuidados", "category": "Beleza", "slug": "beleza", "emoji": "💄", "channel": "Beleza e Cuidados", "time": "12:00 - 15:00"},
    {"label": "Cupons e Promoções", "category": "Supermercados", "slug": "supermercados", "emoji": "🛒", "channel": "Cupons e Promoções", "time": "08:00 - 10:00"},
    {"label": "Ofertas Pet", "category": "Pet", "slug": "pet", "emoji": "🐶", "channel": "Ofertas Pet", "time": "17:00 - 20:00"},
    {"label": "Moda e Calçados", "category": "Calçados", "slug": "calcados", "emoji": "👟", "channel": "Moda e Calçados", "time": "12:00 - 15:00"},
    {"label": "Saúde", "category": "Saúde", "slug": "saude", "emoji": "❤️", "channel": "Saúde e Bem-estar", "time": "09:00 - 11:00"},
]

ALIASES = {
    "Roupas Femininas": "Moda Feminina",
    "Roupas Masculinas": "Moda Masculina",
    "Roupas Plus Size": "Moda Plus Size",
    "Moda infantil": "Moda Infantil",
    "Sapatos": "Calçados",
    "Sapatos Femininos": "Calçados",
    "Sapatos Masculinos": "Calçados",
    "Esportes e Lazer": "Esportes",
    "Jogos e Consoles": "Games",
    "Mae e Bebe": "Mãe e Bebê",
    "Saude": "Saúde",
    "Informatica": "Informática",
    "Eletronicos": "Eletrônicos",
}


def normalize(value):
    text = str(value or "")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def canonical_category(offer):
    raw = str(offer.get("category") or "Outros").strip()
    raw = ALIASES.get(raw, raw)

    title = offer.get("title") or ""
    desc = offer.get("description") or ""
    text = normalize(f"{title} {desc} {raw}")

    if any(t in text for t in ["fralda", "pampers", "huggies", "mamypoko", "mamy poko", "lenco umedecido", "bebe", "baby"]):
        return "Mãe e Bebê"

    if any(t in text for t in ["smartphone", "celular", "iphone", "xiaomi", "redmi", "galaxy", "motorola", "android", "5g"]):
        return "Celulares"

    if any(t in text for t in ["notebook", "laptop", "ssd", "ryzen", "rtx", "gtx", "monitor gamer", "teclado", "mouse", "impressora"]):
        return "Informática"

    if any(t in text for t in ["air fryer", "panela", "liquidificador", "cafeteira", "cozinha", "rack para tv", "painel para tv"]):
        return "Casa e Cozinha"

    if any(t in text for t in ["barbeador", "perfume", "secador", "chapinha", "escova secadora", "maquiagem", "shampoo"]):
        return "Beleza"

    if any(t in text for t in ["racao", "cachorro", "gato", "areia higienica", "pet"]):
        return "Pet"

    if any(t in text for t in ["monitor de pressao", "pressao arterial", "termometro", "inalador", "oximetro", "glicose"]):
        return "Saúde"

    if any(t in text for t in ["tenis", "sapato", "sandalia", "chinelo", "bota", "calcado"]):
        return "Calçados"

    if any(t in text for t in ["mochila", "bolsa", "mala", "necessaire"]):
        return "Bolsas"

    if any(t in text for t in ["short feminino", "shorts feminino", "shorts femininos", "blusa feminina", "regata feminina", "top feminino", "cropped", "legging", "feminina", "feminino", "mulher"]):
        return "Moda Feminina"

    return raw


def parse_money(value):
    if value is None or value == "":
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace("R$", "").replace(" ", "")

    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")

    text = re.sub(r"[^0-9.]", "", text)

    try:
        return float(text)
    except Exception:
        return None


def brl(value):
    number = parse_money(value)

    if not number:
        return ""

    formatted = f"{number:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def price(offer):
    return (
        offer.get("price_text")
        or offer.get("formatted_price")
        or brl(offer.get("current_price"))
        or brl(offer.get("sale_price"))
        or brl(offer.get("price"))
        or "Ver preço"
    )


def old_price(offer):
    return (
        offer.get("old_price_text")
        or offer.get("original_price_text")
        or brl(offer.get("old_price"))
        or brl(offer.get("original_price"))
        or ""
    )


def offer_url(offer):
    return (
        offer.get("affiliate_url")
        or offer.get("url")
        or offer.get("link")
        or offer.get("product_url")
        or "#"
    )


def marketplace(offer):
    raw = str(offer.get("marketplace") or "Oferta").strip()
    key = normalize(raw).replace(" ", "")

    labels = {
        "mercadolivre": "Mercado Livre",
        "ml": "Mercado Livre",
        "shopee": "Shopee",
        "amazon": "Amazon",
        "aliexpress": "AliExpress",
    }

    return labels.get(key, raw)


def discount_number(offer):
    try:
        return float(offer.get("discount_percent") or 0)
    except Exception:
        return 0.0


def discount_label(offer):
    d = discount_number(offer)

    if d > 0:
        return f"{d:.0f}% OFF"

    return "Oferta"


def short(value, limit=92):
    text = str(value or "").strip()

    if len(text) <= limit:
        return text

    return text[:limit - 1].rstrip() + "…"


def score_offer(offer):
    score = 0

    d = discount_number(offer)

    if d >= 60:
        score += 35
    elif d >= 40:
        score += 25
    elif d >= 20:
        score += 15

    if price(offer):
        score += 10

    title = normalize(offer.get("title") or "")

    hot = [
        "fralda", "pampers", "huggies", "mamypoko", "air fryer", "panela",
        "smartphone", "celular", "xiaomi", "samsung", "notebook", "ssd",
        "perfume", "barbeador", "secador", "chapinha", "racao", "pet"
    ]

    if any(t in title for t in hot):
        score += 20

    return score


def load_offers():
    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        raise SystemExit("data/offers.json não é lista.")

    for offer in offers:
        offer["_category"] = canonical_category(offer)
        offer["_growth_score"] = score_offer(offer)

    offers.sort(key=lambda o: o.get("_growth_score") or 0, reverse=True)

    return offers


def top_offer_for_category(offers, category):
    pool = [offer for offer in offers if offer.get("_category") == category]

    if not pool:
        return None

    pool.sort(key=lambda o: o.get("_growth_score") or 0, reverse=True)

    return pool[0]


def whatsapp_text(item, offer):
    title = offer.get("title") or "Oferta"
    current = price(offer)
    old = old_price(offer)
    url = offer_url(offer)
    mp = marketplace(offer)
    disc = discount_label(offer)

    lines = []

    lines.append(f"{item['emoji']} Oferta para {item['label']}")
    lines.append("")
    lines.append(short(title, 120))
    lines.append("")

    if old:
        lines.append(f"💸 De: {old}")

    lines.append(f"🔥 Por: {current}")

    if disc != "Oferta":
        lines.append(f"🏷️ {disc}")

    lines.append(f"🛒 Loja: {mp}")
    lines.append("")
    lines.append(f"Ver oferta: {url}")
    lines.append("")
    lines.append("⚠️ Preço e disponibilidade podem mudar.")
    lines.append("MaryLouse Ofertas pode receber comissão por compras feitas pelos links.")

    return "\n".join(lines)


def build_recommendations(offers):
    recommendations = []
    used_links = set()

    for item in CATEGORY_DEFS:
        offer = top_offer_for_category(offers, item["category"])

        if not offer:
            continue

        url = offer_url(offer)

        if url in used_links:
            continue

        used_links.add(url)

        card = f"{SITE_URL}/growth/pinterest/{item['slug']}.png"

        recommendations.append({
            "channel": item["channel"],
            "category": item["label"],
            "time": item["time"],
            "title": offer.get("title") or "Oferta",
            "price": price(offer),
            "marketplace": marketplace(offer),
            "link": url,
            "image": card,
            "text": whatsapp_text(item, offer),
            "score": offer.get("_growth_score") or 0,
        })

    # Começar leve: máximo 6 sugestões por dia.
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return recommendations[:6]


def write_markdown(recommendations):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    lines = []
    lines.append("# WhatsApp Pack do Dia — MaryLouse Ofertas")
    lines.append("")
    lines.append(f"Gerado em: {now}")
    lines.append("")
    lines.append("## Como usar")
    lines.append("")
    lines.append("1. Abra a comunidade MaryLouse Ofertas no WhatsApp.")
    lines.append("2. Escolha o canal recomendado.")
    lines.append("3. Envie a imagem indicada.")
    lines.append("4. Copie e cole o texto pronto.")
    lines.append("5. Comece com 3 a 5 posts por dia para evitar excesso.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, item in enumerate(recommendations, start=1):
        lines.append(f"## Post {i} — {item['category']}")
        lines.append("")
        lines.append(f"**Canal recomendado:** {item['channel']}")
        lines.append("")
        lines.append(f"**Horário sugerido:** {item['time']}")
        lines.append("")
        lines.append(f"**Imagem/card:**")
        lines.append("")
        lines.append(item["image"])
        lines.append("")
        lines.append(f"**Texto pronto:**")
        lines.append("")
        lines.append("```txt")
        lines.append(item["text"])
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    out = OUTPUT_DIR / "whatsapp_today.md"
    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"OK: {out}")


def write_csv(recommendations):
    out = OUTPUT_DIR / "whatsapp_today.csv"

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["channel", "category", "time", "title", "price", "marketplace", "link", "image", "text", "score"],
            delimiter=";"
        )
        writer.writeheader()
        writer.writerows(recommendations)

    print(f"OK: {out} | {len(recommendations)} posts")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    offers = load_offers()
    recommendations = build_recommendations(offers)

    write_markdown(recommendations)
    write_csv(recommendations)

    print("WhatsApp Pack gerado com sucesso.")


if __name__ == "__main__":
    main()
