from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
import csv
import json
import re
import unicodedata


SITE_URL = "https://marylouse-ofertas.vercel.app"

OFFERS_PATH = Path("data/offers.json")
OUTPUT_DIR = Path("growth/output")


CATEGORY_DEFS = [
    {"label": "Supermercados", "category": "Supermercados", "slug": "supermercados", "emoji": "🛒", "board": "Cupons e Promoções"},
    {"label": "Celulares", "category": "Celulares", "slug": "celulares", "emoji": "📱", "board": "Celulares e Tecnologia"},
    {"label": "Eletrônicos", "category": "Eletrônicos", "slug": "eletronicos", "emoji": "🎧", "board": "Celulares e Tecnologia"},
    {"label": "Informática", "category": "Informática", "slug": "informatica", "emoji": "💻", "board": "Celulares e Tecnologia"},
    {"label": "Games", "category": "Games", "slug": "games", "emoji": "🎮", "board": "Celulares e Tecnologia"},
    {"label": "Casa e Cozinha", "category": "Casa e Cozinha", "slug": "casa-cozinha", "emoji": "🍳", "board": "Achadinhos de Casa"},
    {"label": "Eletrodomésticos", "category": "Eletrodomésticos", "slug": "eletrodomesticos", "emoji": "🔌", "board": "Achadinhos de Casa"},
    {"label": "Moda Feminina", "category": "Moda Feminina", "slug": "moda-feminina", "emoji": "👗", "board": "Moda e Calçados"},
    {"label": "Moda Masculina", "category": "Moda Masculina", "slug": "moda-masculina", "emoji": "👕", "board": "Moda e Calçados"},
    {"label": "Moda Plus Size", "category": "Moda Plus Size", "slug": "moda-plus-size", "emoji": "✨", "board": "Moda e Calçados"},
    {"label": "Moda Infantil", "category": "Moda Infantil", "slug": "moda-infantil", "emoji": "🧒", "board": "Moda e Calçados"},
    {"label": "Calçados", "category": "Calçados", "slug": "calcados", "emoji": "👟", "board": "Moda e Calçados"},
    {"label": "Bolsas", "category": "Bolsas", "slug": "bolsas", "emoji": "👜", "board": "Moda e Calçados"},
    {"label": "Beleza", "category": "Beleza", "slug": "beleza", "emoji": "💄", "board": "Beleza e Cuidados"},
    {"label": "Esportes", "category": "Esportes", "slug": "esportes", "emoji": "🏋️", "board": "MaryLouse Ofertas"},
    {"label": "Brinquedos", "category": "Brinquedos e Hobbies", "slug": "brinquedos", "emoji": "🧸", "board": "Ofertas para Bebê"},
    {"label": "Mãe e Bebê", "category": "Mãe e Bebê", "slug": "mae-bebe", "emoji": "🍼", "board": "Ofertas para Bebê"},
    {"label": "Pet", "category": "Pet", "slug": "pet", "emoji": "🐶", "board": "Ofertas Pet"},
    {"label": "Saúde", "category": "Saúde", "slug": "saude", "emoji": "❤️", "board": "Beleza e Cuidados"},
    {"label": "Papelaria", "category": "Papelaria", "slug": "papelaria", "emoji": "📚", "board": "MaryLouse Ofertas"},
    {"label": "Ferramentas", "category": "Ferramentas", "slug": "ferramentas", "emoji": "🧰", "board": "MaryLouse Ofertas"},
    {"label": "Outros", "category": "Outros", "slug": "outros", "emoji": "📦", "board": "MaryLouse Ofertas"},
]

CATEGORY_BY_NAME = {c["category"]: c for c in CATEGORY_DEFS}

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


PRIORITY_CATEGORIES = [
    "Mãe e Bebê",
    "Casa e Cozinha",
    "Beleza",
    "Celulares",
    "Supermercados",
    "Pet",
    "Saúde",
    "Calçados",
    "Moda Feminina",
    "Informática",
]


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

    if any(t in text for t in ["camiseta masculina", "camisa masculina", "bermuda masculina", "cueca", "masculino", "homem"]):
        return "Moda Masculina"

    return raw if raw in CATEGORY_BY_NAME else "Outros"


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


def parse_ts(offer):
    for key in ["created_ts", "timestamp", "ts"]:
        value = offer.get(key)

        if value:
            try:
                value = float(value)

                if value > 1000000000000:
                    value = value / 1000

                return int(value)
            except Exception:
                pass

    for key in ["created_at_iso", "created_at", "published_at", "posted_at", "collected_at"]:
        value = offer.get(key)

        if not value:
            continue

        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return int(dt.timestamp())
        except Exception:
            pass

    return 0


def short(value, limit=95):
    text = str(value or "").strip()

    if len(text) <= limit:
        return text

    return text[:limit - 1].rstrip() + "…"


def category_page_url(cat, source="pinterest", medium="organic"):
    params = urlencode({
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": f"pin_{cat['slug']}",
    })

    return f"{SITE_URL}/ofertas-{cat['slug']}.html?{params}"


def card_url(cat):
    return f"{SITE_URL}/growth/pinterest/{cat['slug']}.png"


def load_offers():
    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        raise SystemExit("data/offers.json não é lista.")

    for offer in offers:
        offer["_category"] = canonical_category(offer)
        offer["_created_ts"] = parse_ts(offer)

    offers.sort(key=lambda o: o.get("_created_ts") or 0, reverse=True)

    return offers


def growth_score(offer):
    score = 0

    category = offer.get("_category") or "Outros"

    if category in PRIORITY_CATEGORIES:
        score += 35

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

    hot_terms = [
        "fralda", "pampers", "huggies", "mamypoko", "air fryer", "panela",
        "smartphone", "celular", "xiaomi", "samsung", "notebook", "ssd",
        "perfume", "barbeador", "secador", "chapinha", "racao", "papel higienico"
    ]

    if any(t in title for t in hot_terms):
        score += 20

    return score


def top_offers(offers, category=None, limit=5):
    pool = []

    for offer in offers:
        if category and offer.get("_category") != category:
            continue

        offer["_growth_score"] = growth_score(offer)
        pool.append(offer)

    pool.sort(key=lambda o: o.get("_growth_score") or 0, reverse=True)

    return pool[:limit]


def build_category_recommendations(offers, max_items=4):
    counts = {}

    for offer in offers:
        cat = offer.get("_category") or "Outros"
        counts[cat] = counts.get(cat, 0) + 1

    recommendations = []

    for cat_name in PRIORITY_CATEGORIES:
        cat = CATEGORY_BY_NAME.get(cat_name)

        if not cat:
            continue

        category_offers = top_offers(offers, cat_name, limit=1)

        if not category_offers:
            continue

        top = category_offers[0]

        recommendations.append({
            "type": "categoria",
            "board": cat["board"],
            "category": cat["label"],
            "title": f"{cat['emoji']} Ofertas de {cat['label']} atualizadas hoje",
            "description": (
                f"Veja ofertas de {cat['label']} selecionadas pela MaryLouse Ofertas. "
                f"Destaque de hoje: {short(top.get('title'), 80)}. "
                f"Preço e disponibilidade podem mudar. Podemos receber comissão por compras feitas pelos links."
            ),
            "link": category_page_url(cat),
            "image": card_url(cat),
            "why": f"Categoria com {counts.get(cat_name, 0)} oferta(s) e boa intenção de compra.",
        })

        if len(recommendations) >= max_items:
            break

    return recommendations


def build_direct_offer_recommendations(offers, max_items=2):
    pool = []

    for offer in offers:
        if not offer_url(offer) or not offer.get("title"):
            continue

        offer["_growth_score"] = growth_score(offer)
        pool.append(offer)

    pool.sort(key=lambda o: o.get("_growth_score") or 0, reverse=True)

    recommendations = []
    used_categories = set()

    for offer in pool:
        cat_name = offer.get("_category") or "Outros"

        if cat_name in used_categories:
            continue

        cat = CATEGORY_BY_NAME.get(cat_name, CATEGORY_BY_NAME["Outros"])

        recommendations.append({
            "type": "produto_direto",
            "board": cat["board"],
            "category": cat["label"],
            "title": f"{discount_label(offer)}: {short(offer.get('title'), 70)}",
            "description": (
                f"Oferta destaque em {cat['label']} encontrada pela MaryLouse Ofertas. "
                f"Preço: {price(offer)}. Loja: {marketplace(offer)}. "
                f"Preço e disponibilidade podem mudar. Podemos receber comissão por compras feitas pelos links."
            ),
            "link": offer_url(offer),
            "image": card_url(cat),
            "why": f"Produto com bom score orgânico ({offer.get('_growth_score')}) e link direto afiliado.",
        })

        used_categories.add(cat_name)

        if len(recommendations) >= max_items:
            break

    return recommendations


def write_markdown(recommendations):
    today = datetime.now().strftime("%d/%m/%Y %H:%M")

    lines = []
    lines.append("# Pinterest Pack do Dia — MaryLouse Ofertas")
    lines.append("")
    lines.append(f"Gerado em: {today}")
    lines.append("")
    lines.append("## Como usar")
    lines.append("")
    lines.append("1. Abra o Pinterest Business.")
    lines.append("2. Clique em **Criar Pin**.")
    lines.append("3. Use a imagem indicada.")
    lines.append("4. Copie o título, descrição e link.")
    lines.append("5. Publique no board sugerido.")
    lines.append("")
    lines.append("Recomendação inicial: publicar de 3 a 5 pins por dia.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, item in enumerate(recommendations, start=1):
        lines.append(f"## Pin {i} — {item['category']}")
        lines.append("")
        lines.append(f"**Tipo:** {item['type']}")
        lines.append("")
        lines.append(f"**Board sugerido:** {item['board']}")
        lines.append("")
        lines.append(f"**Imagem para upload no Pinterest:**")
        lines.append("")
        lines.append(item["image"])
        lines.append("")
        lines.append(f"**Título:**")
        lines.append("")
        lines.append(item["title"])
        lines.append("")
        lines.append(f"**Descrição:**")
        lines.append("")
        lines.append(item["description"])
        lines.append("")
        lines.append(f"**Link de destino do Pin:**")
        lines.append("")
        lines.append(item["link"])
        lines.append("")
        lines.append(f"**Por que postar:**")
        lines.append("")
        lines.append(item["why"])
        lines.append("")
        lines.append("---")
        lines.append("")

    out = OUTPUT_DIR / "pinterest_today.md"
    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"OK: {out}")


def write_csv(recommendations):
    out = OUTPUT_DIR / "pinterest_today.csv"

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["type", "board", "category", "title", "description", "link", "image", "why"],
            delimiter=";"
        )
        writer.writeheader()
        writer.writerows(recommendations)

    print(f"OK: {out} | {len(recommendations)} pins")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    offers = load_offers()

    category_pins = build_category_recommendations(offers, max_items=4)
    direct_pins = build_direct_offer_recommendations(offers, max_items=2)

    recommendations = category_pins + direct_pins

    # Limita em 5 para começar sem parecer spam.
    recommendations = recommendations[:5]

    write_markdown(recommendations)
    write_csv(recommendations)

    print("Pinterest Pack gerado com sucesso.")


if __name__ == "__main__":
    main()
