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
    {"label": "Supermercados", "category": "Supermercados", "slug": "supermercados", "emoji": "🛒"},
    {"label": "Celulares", "category": "Celulares", "slug": "celulares", "emoji": "📱"},
    {"label": "Eletrônicos", "category": "Eletrônicos", "slug": "eletronicos", "emoji": "🎧"},
    {"label": "Informática", "category": "Informática", "slug": "informatica", "emoji": "💻"},
    {"label": "Games", "category": "Games", "slug": "games", "emoji": "🎮"},
    {"label": "Casa e Cozinha", "category": "Casa e Cozinha", "slug": "casa-cozinha", "emoji": "🍳"},
    {"label": "Eletrodomésticos", "category": "Eletrodomésticos", "slug": "eletrodomesticos", "emoji": "🔌"},
    {"label": "Moda Feminina", "category": "Moda Feminina", "slug": "moda-feminina", "emoji": "👗"},
    {"label": "Moda Masculina", "category": "Moda Masculina", "slug": "moda-masculina", "emoji": "👕"},
    {"label": "Moda Plus Size", "category": "Moda Plus Size", "slug": "moda-plus-size", "emoji": "✨"},
    {"label": "Moda Infantil", "category": "Moda Infantil", "slug": "moda-infantil", "emoji": "🧒"},
    {"label": "Calçados", "category": "Calçados", "slug": "calcados", "emoji": "👟"},
    {"label": "Bolsas", "category": "Bolsas", "slug": "bolsas", "emoji": "👜"},
    {"label": "Beleza", "category": "Beleza", "slug": "beleza", "emoji": "💄"},
    {"label": "Esportes", "category": "Esportes", "slug": "esportes", "emoji": "🏋️"},
    {"label": "Brinquedos", "category": "Brinquedos e Hobbies", "slug": "brinquedos", "emoji": "🧸"},
    {"label": "Mãe e Bebê", "category": "Mãe e Bebê", "slug": "mae-bebe", "emoji": "🍼"},
    {"label": "Pet", "category": "Pet", "slug": "pet", "emoji": "🐶"},
    {"label": "Saúde", "category": "Saúde", "slug": "saude", "emoji": "❤️"},
    {"label": "Papelaria", "category": "Papelaria", "slug": "papelaria", "emoji": "📚"},
    {"label": "Ferramentas", "category": "Ferramentas", "slug": "ferramentas", "emoji": "🧰"},
    {"label": "Outros", "category": "Outros", "slug": "outros", "emoji": "📦"},
]

ALIASES = {
    "Roupas Femininas": "Moda Feminina",
    "Roupas Masculinas": "Moda Masculina",
    "Roupas Plus Size": "Moda Plus Size",
    "Moda infantil": "Moda Infantil",
    "Sapatos": "Calçados",
    "Esportes e Lazer": "Esportes",
    "Jogos e Consoles": "Games",
    "Mae e Bebe": "Mãe e Bebê",
    "Saude": "Saúde",
    "Informatica": "Informática",
    "Eletronicos": "Eletrônicos",
}

CATEGORY_BY_NAME = {c["category"]: c for c in CATEGORY_DEFS}


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


def offer_url(offer):
    return (
        offer.get("affiliate_url")
        or offer.get("url")
        or offer.get("link")
        or offer.get("product_url")
        or "#"
    )


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


def short(value, limit=90):
    text = str(value or "").strip()

    if len(text) <= limit:
        return text

    return text[:limit - 1].rstrip() + "…"


def category_page_url(cat, source, medium, campaign):
    params = urlencode({
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
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

    category = offer.get("_category")

    if category in {"Mãe e Bebê", "Supermercados", "Casa e Cozinha", "Celulares", "Informática", "Beleza", "Pet", "Saúde"}:
        score += 30

    d = discount_number(offer)

    if d >= 50:
        score += 30
    elif d >= 30:
        score += 20
    elif d >= 15:
        score += 10

    if price(offer):
        score += 10

    title = normalize(offer.get("title") or "")

    hot = [
        "fralda", "pampers", "huggies", "air fryer", "smartphone", "celular",
        "xiaomi", "notebook", "ssd", "perfume", "barbeador", "racao",
        "papel higienico", "panela", "secador", "chapinha"
    ]

    if any(t in title for t in hot):
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


def write_social_posts(offers, counts):
    rows = []

    for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        cat = CATEGORY_BY_NAME.get(category)

        if not cat or count <= 0:
            continue

        top = top_offers(offers, category, limit=1)
        offer = top[0] if top else None

        campaign = f"social_{cat['slug']}"
        url = category_page_url(cat, "social", "organic", campaign)

        if offer:
            caption = (
                f"{cat['emoji']} Ofertas de {cat['label']} atualizadas hoje!\\n\\n"
                f"Destaque: {offer.get('title')}\\n"
                f"Preço: {price(offer)}\\n\\n"
                f"Veja a seleção completa:\\n{url}"
            )
        else:
            caption = (
                f"{cat['emoji']} Ofertas de {cat['label']} atualizadas hoje!\\n\\n"
                f"Confira os achadinhos da MaryLouse:\\n{url}"
            )

        hashtags = hashtags_for_category(category)

        for platform in ["Instagram", "Facebook", "Threads", "WhatsApp Status"]:
            rows.append({
                "platform": platform,
                "category": cat["label"],
                "title": f"{cat['emoji']} Ofertas de {cat['label']} hoje",
                "caption": caption,
                "hashtags": hashtags,
                "url": url,
                "card_url": card_url(cat),
            })

    out = OUTPUT_DIR / "social_posts.csv"

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["platform", "category", "title", "caption", "hashtags", "url", "card_url"],
            delimiter=";"
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK: {out} | {len(rows)} posts")


def write_pinterest_pins(offers, counts):
    rows = []

    for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        cat = CATEGORY_BY_NAME.get(category)

        if not cat or count <= 0:
            continue

        top = top_offers(offers, category, limit=1)
        offer = top[0] if top else None

        # Para Pinterest, testaremos link direto afiliado do produto destaque.
        url = offer_url(offer) if offer else category_page_url(cat, "pinterest", "organic", f"pin_{cat['slug']}")

        rows.append({
            "board": "MaryLouse Ofertas",
            "category": cat["label"],
            "title": f"{cat['emoji']} {cat['label']}: oferta destaque de hoje",
            "description": f"Oferta selecionada pela MaryLouse em {cat['label']}. Confira antes que mude. Preço e disponibilidade podem variar.",
            "link": url,
            "image": card_url(cat),
            "keywords": f"ofertas, promoção, achadinhos, {cat['label']}",
        })

    out = OUTPUT_DIR / "pinterest_pins.csv"

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["board", "category", "title", "description", "link", "image", "keywords"],
            delimiter=";"
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK: {out} | {len(rows)} pins")


def write_telegram_digest(offers):
    top = top_offers(offers, limit=8)

    lines = []
    lines.append("🔥 Top ofertas MaryLouse de hoje")
    lines.append("")
    lines.append("Ofertas selecionadas por desconto, recência e intenção de compra.")
    lines.append("")

    for i, offer in enumerate(top, start=1):
        lines.append(f"{i}. {short(offer.get('title'), 80)}")
        lines.append(f"   {offer.get('_category')} | {price(offer)}")
        lines.append(f"   {offer_url(offer)}")
        lines.append("")

    lines.append("🧭 Ver todas as categorias:")
    lines.append(f"{SITE_URL}/?utm_source=telegram&utm_medium=organic&utm_campaign=digest_diario#categorias")
    lines.append("")
    lines.append("Aviso: podemos receber comissão por compras feitas pelos links.")

    out = OUTPUT_DIR / "telegram_digest.txt"
    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"OK: {out}")


def write_daily_plan(offers, counts):
    ranked_categories = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_global = top_offers(offers, limit=10)

    lines = []
    lines.append("# Plano Diário de Divulgação Orgânica — MaryLouse Ofertas")
    lines.append("")
    lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append("")
    lines.append("## Categorias prioritárias")
    lines.append("")

    for category, count in ranked_categories[:10]:
        cat = CATEGORY_BY_NAME.get(category)

        if not cat:
            continue

        url = category_page_url(cat, "daily_plan", "organic", f"categoria_{cat['slug']}")
        lines.append(f"- {cat['emoji']} **{cat['label']}**: {count} oferta(s) — {url}")

    lines.append("")
    lines.append("## Top ofertas para destacar")
    lines.append("")

    for i, offer in enumerate(top_global, start=1):
        lines.append(f"{i}. **{short(offer.get('title'), 100)}**")
        lines.append(f"   - Categoria: {offer.get('_category')}")
        lines.append(f"   - Loja: {marketplace(offer)}")
        lines.append(f"   - Preço: {price(offer)}")
        lines.append(f"   - Desconto: {discount_label(offer)}")
        lines.append(f"   - Link: {offer_url(offer)}")
        lines.append("")

    lines.append("## Ações gratuitas recomendadas")
    lines.append("")
    lines.append("1. Publicar 3 pins no Pinterest usando `growth/output/pinterest_pins.csv`.")
    lines.append("2. Publicar 2 posts sociais usando `growth/output/social_posts.csv`.")
    lines.append("3. Usar `growth/output/telegram_digest.txt` como resumo diário no Telegram.")
    lines.append("4. Priorizar categorias com maior intenção de compra: Bebê, Casa, Supermercado, Beleza, Celulares e Pet.")

    out = OUTPUT_DIR / "daily_growth_plan.md"
    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"OK: {out}")


def hashtags_for_category(category):
    base = ["#MaryLouseOfertas", "#Ofertas", "#Promocao", "#Achadinhos"]

    extra = {
        "Mãe e Bebê": ["#Fraldas", "#Bebe", "#Maternidade"],
        "Casa e Cozinha": ["#Casa", "#Cozinha", "#AchadinhosDeCasa"],
        "Celulares": ["#Celular", "#Smartphone", "#Tecnologia"],
        "Informática": ["#Informatica", "#Notebook", "#Setup"],
        "Beleza": ["#Beleza", "#Skincare", "#Cabelo"],
        "Supermercados": ["#Supermercado", "#Economia", "#Limpeza"],
        "Calçados": ["#Calcados", "#Tenis", "#Moda"],
        "Moda Feminina": ["#ModaFeminina", "#Look", "#Moda"],
        "Moda Masculina": ["#ModaMasculina", "#Moda"],
        "Pet": ["#Pet", "#Caes", "#Gatos"],
    }

    return " ".join(base + extra.get(category, []))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    offers = load_offers()

    counts = {}

    for offer in offers:
        cat = offer.get("_category") or "Outros"
        counts[cat] = counts.get(cat, 0) + 1

    write_social_posts(offers, counts)
    write_pinterest_pins(offers, counts)
    write_telegram_digest(offers)
    write_daily_plan(offers, counts)

    print("Plano diário orgânico concluído.")


if __name__ == "__main__":
    main()
