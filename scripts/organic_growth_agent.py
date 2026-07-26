from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
import csv
import html
import json
import re
import unicodedata
import xml.sax.saxutils as xml_escape


SITE_URL = "https://marylouse-ofertas.vercel.app"

ROOT = Path(".")
OFFERS_PATH = ROOT / "data" / "offers.json"
OUTPUT_DIR = ROOT / "growth" / "output"
CARDS_DIR = ROOT / "growth" / "cards"


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


SEO_INTENTS = {
    "Supermercados": ["promoção supermercado", "ofertas limpeza", "papel higiênico promoção", "sabão em pó promoção"],
    "Celulares": ["celular promoção", "smartphone barato", "xiaomi promoção", "samsung promoção"],
    "Eletrônicos": ["eletrônicos promoção", "gadgets úteis", "fone bluetooth promoção"],
    "Informática": ["notebook promoção", "ssd promoção", "monitor promoção", "periféricos promoção"],
    "Games": ["games promoção", "controle gamer promoção", "console promoção"],
    "Casa e Cozinha": ["air fryer promoção", "panela promoção", "achadinhos casa", "utensílios cozinha"],
    "Eletrodomésticos": ["eletrodomésticos promoção", "aspirador promoção", "ventilador promoção"],
    "Moda Feminina": ["moda feminina promoção", "roupas femininas promoção", "legging promoção"],
    "Moda Masculina": ["moda masculina promoção", "camiseta masculina promoção"],
    "Moda Plus Size": ["moda plus size promoção", "roupas plus size promoção"],
    "Moda Infantil": ["moda infantil promoção", "roupa infantil promoção"],
    "Calçados": ["tênis promoção", "calçados promoção", "sandália promoção"],
    "Bolsas": ["bolsas promoção", "mochilas promoção", "malas promoção"],
    "Beleza": ["beleza promoção", "perfume promoção", "secador promoção", "chapinha promoção"],
    "Esportes": ["fitness promoção", "academia promoção", "halter promoção", "bike spinning promoção"],
    "Brinquedos e Hobbies": ["brinquedos promoção", "hot wheels promoção", "jogos infantis promoção"],
    "Mãe e Bebê": ["fralda promoção", "pampers promoção", "huggies promoção", "lenço umedecido promoção"],
    "Pet": ["ração promoção", "produtos pet promoção", "areia higiênica promoção"],
    "Saúde": ["monitor de pressão promoção", "termômetro promoção", "inalador promoção"],
    "Papelaria": ["papelaria promoção", "material escolar promoção", "canetas promoção"],
    "Ferramentas": ["ferramentas promoção", "furadeira promoção", "parafusadeira promoção"],
    "Outros": ["ofertas online", "achadinhos do dia"],
}


ALIASES = {
    "Eletronicos": "Eletrônicos",
    "EletrÃ´nicos": "Eletrônicos",
    "Informatica": "Informática",
    "Computadores e Acessórios": "Informática",
    "Computadores e Acessorios": "Informática",
    "Jogos e Consoles": "Games",
    "Eletrodomesticos": "Eletrodomésticos",
    "Roupas Femininas": "Moda Feminina",
    "Roupas Masculinas": "Moda Masculina",
    "Roupas Plus Size": "Moda Plus Size",
    "Moda infantil": "Moda Infantil",
    "Sapatos": "Calçados",
    "Sapatos Femininos": "Calçados",
    "Sapatos Masculinos": "Calçados",
    "Esportes e Lazer": "Esportes",
    "Mae e Bebe": "Mãe e Bebê",
    "Saude": "Saúde",
    "Toys": "Brinquedos e Hobbies",
    "Toys & Games": "Brinquedos e Hobbies",
}


def strip_accents(value):
    text = str(value or "")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def normalize(value):
    text = strip_accents(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def has(text, words):
    return any(normalize(word) in text for word in words)


def canonical_category(offer):
    raw = str(offer.get("category") or "").strip()
    title = offer.get("title") or offer.get("raw_title") or offer.get("name") or ""
    desc = offer.get("description") or ""
    marketplace = offer.get("marketplace") or ""

    text = normalize(" ".join([title, desc, raw, marketplace]))

    if has(text, ["monitor de pressao", "pressao arterial", "termometro", "inalador", "nebulizador", "oximetro", "glicose", "bioimpedancia"]):
        return "Saúde"

    if has(text, ["notebook", "laptop", "asus tuf", "tuf gaming", "rtx", "gtx", "geforce", "ryzen", "processador", "ssd", "memoria ram", "teclado", "mouse", "impressora"]):
        return "Informática"

    if has(text, ["smartphone", "celular", "iphone", "galaxy", "xiaomi", "redmi", "poco", "motorola", "android", "5g"]):
        return "Celulares"

    if has(text, ["fralda", "pampers", "huggies", "mamypoko", "mamy poko", "lenco umedecido", "mamadeira", "chupeta", "bebe", "baby"]):
        return "Mãe e Bebê"

    if has(text, ["mochila", "bolsa", "mala", "necessaire", "pochete", "carteira", "backpack", "maleta"]):
        return "Bolsas"

    if has(text, ["tenis", "sapato", "sandalia", "chinelo", "bota", "sneaker", "calcado"]):
        return "Calçados"

    if has(text, ["painel para tv", "rack para tv", "rack para sala", "cadeira escritorio", "mesa computador", "escrivaninha", "fruteira", "cesto multiuso", "organizador de cozinha"]):
        return "Casa e Cozinha"

    if has(text, ["barbeador", "aparador", "perfume", "hidratante", "shampoo", "condicionador", "maquiagem", "secador", "chapinha", "escova secadora"]):
        return "Beleza"

    if has(text, ["air fryer", "panela", "frigideira", "cafeteira", "liquidificador", "batedeira", "mixer", "microondas", "garrafa", "copo", "cozinha"]):
        return "Casa e Cozinha"

    if has(text, ["geladeira", "fogao", "cooktop", "lavadora", "maquina de lavar", "ar condicionado", "ventilador", "aspirador de po"]):
        return "Eletrodomésticos"

    if has(text, ["racao", "cachorro", "gato", "areia higienica", "coleira", "arranhador", "bebedouro pet"]) or " pet " in f" {text} ":
        return "Pet"

    if has(text, ["papel higienico", "detergente", "amaciante", "sabao em po", "sabonete", "creme dental", "papel toalha", "arroz", "feijao", "azeite", "supermercado"]):
        return "Supermercados"

    if has(text, ["playstation", "ps5", "xbox", "nintendo", "console", "controle gamer", "joystick", "videogame"]):
        return "Games"

    if has(text, ["hot wheels", "lego", "boneca", "boneco", "brinquedo", "jogo da forca", "quebra cabeca"]):
        return "Brinquedos e Hobbies"

    if has(text, ["halter", "academia", "fitness", "bike spinning", "bicicleta", "bola futebol", "yoga", "whey", "creatina", "esteira", "corrida"]):
        return "Esportes"

    if has(text, ["caneta", "lapis", "caderno", "agenda", "marca texto", "papel sulfite", "estojo escolar", "papelaria"]):
        return "Papelaria"

    if has(text, ["furadeira", "parafusadeira", "chave de fenda", "martelo", "serra", "trena", "alicate", "ferramenta"]):
        return "Ferramentas"

    if has(text, ["plus size"]):
        return "Moda Plus Size"

    if has(text, ["vestido", "blusa feminina", "cropped", "saia", "legging", "top feminino", "conjunto feminino"]):
        return "Moda Feminina"

    if has(text, ["camiseta masculina", "camisa masculina", "calca masculina", "bermuda masculina", "cueca", "masculino"]):
        return "Moda Masculina"

    if has(text, ["infantil", "menino", "menina", "crianca", "kids", "roupa infantil"]):
        return "Moda Infantil"

    return ALIASES.get(raw, raw if raw else "Outros")


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
            text = str(value).replace("Z", "+00:00")
            dt = datetime.fromisoformat(text)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return int(dt.timestamp())
        except Exception:
            pass

    return 0


def parse_money(value):
    if value is None or value == "":
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    text = text.replace("R$", "").replace(" ", "")

    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")

    text = re.sub(r"[^0-9.]", "", text)

    if text.count(".") > 1:
        parts = text.split(".")
        text = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return float(text)
    except Exception:
        return None


def format_brl(value):
    number = parse_money(value)

    if number is None or number <= 0:
        return ""

    formatted = f"{number:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def get_price(offer):
    return (
        offer.get("price_text")
        or offer.get("formatted_price")
        or format_brl(offer.get("current_price"))
        or format_brl(offer.get("sale_price"))
        or format_brl(offer.get("price"))
        or ""
    )


def discount_number(offer):
    try:
        return float(offer.get("discount_percent") or 0)
    except Exception:
        return 0.0


def discount_label(offer):
    number = discount_number(offer)

    if number > 0:
        return f"{number:.0f}% OFF"

    return "Oferta"


def offer_url(offer):
    return (
        offer.get("affiliate_url")
        or offer.get("url")
        or offer.get("link")
        or offer.get("product_url")
        or "#"
    )


def marketplace_label(value):
    raw = str(value or "Oferta").strip()
    key = normalize(raw).replace(" ", "")

    labels = {
        "mercadolivre": "Mercado Livre",
        "ml": "Mercado Livre",
        "shopee": "Shopee",
        "amazon": "Amazon",
        "aliexpress": "AliExpress",
    }

    return labels.get(key, raw)


def short(value, limit=120):
    text = str(value or "").strip()

    if len(text) <= limit:
        return text

    return text[:limit - 1].rstrip() + "…"


def page_url_for_category(cat, source, medium, campaign):
    base = f"{SITE_URL}/ofertas-{cat['slug']}.html"
    params = urlencode({
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
    })
    return f"{base}?{params}"


def category_by_name():
    return {cat["category"]: cat for cat in CATEGORY_DEFS}


def load_offers():
    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        raise SystemExit("data/offers.json não é uma lista.")

    for offer in offers:
        offer["_category"] = canonical_category(offer)
        offer["_created_ts"] = parse_ts(offer)

    offers.sort(key=lambda o: o.get("_created_ts") or 0, reverse=True)

    return offers


def offer_growth_score(offer):
    score = 0.0

    category = offer.get("_category") or "Outros"
    discount = discount_number(offer)
    price = parse_money(offer.get("price") or offer.get("current_price") or offer.get("sale_price"))

    high_intent_categories = {
        "Mãe e Bebê", "Supermercados", "Casa e Cozinha", "Celulares",
        "Informática", "Beleza", "Pet", "Saúde"
    }

    if category in high_intent_categories:
        score += 30

    if discount >= 50:
        score += 30
    elif discount >= 30:
        score += 22
    elif discount >= 15:
        score += 14

    if price:
        if 20 <= price <= 300:
            score += 18
        elif 300 < price <= 1500:
            score += 14
        elif 1500 < price <= 5000:
            score += 8

    title = normalize(offer.get("title") or "")

    hot_terms = [
        "fralda", "pampers", "huggies", "mamypoko", "air fryer",
        "smartphone", "celular", "xiaomi", "samsung", "notebook",
        "ssd", "monitor", "perfume", "barbeador", "secador",
        "racao", "papel higienico", "panela", "aspirador"
    ]

    if any(term in title for term in hot_terms):
        score += 20

    ts = offer.get("_created_ts") or 0

    if ts:
        age_hours = max(0, (datetime.now(timezone.utc).timestamp() - ts) / 3600)

        if age_hours <= 3:
            score += 15
        elif age_hours <= 12:
            score += 8

    return round(score, 2)


def top_offers(offers, category=None, limit=5):
    pool = []

    for offer in offers:
        if category and offer.get("_category") != category:
            continue

        if not offer_url(offer) or not offer.get("title"):
            continue

        offer["_growth_score"] = offer_growth_score(offer)
        pool.append(offer)

    pool.sort(key=lambda o: o.get("_growth_score") or 0, reverse=True)

    return pool[:limit]


def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)


def svg_escape(value):
    return html.escape(str(value or ""), quote=True)


def write_svg_card(cat, count, top_offer=None):
    slug = cat["slug"]
    label = cat["label"]
    emoji = cat["emoji"]
    offer_title = short(top_offer.get("title"), 72) if top_offer else "Ofertas atualizadas hoje"
    price = get_price(top_offer) if top_offer else ""
    discount = discount_label(top_offer) if top_offer else "Ofertas"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fff2e8"/>
      <stop offset="55%" stop-color="#fff6fb"/>
      <stop offset="100%" stop-color="#ffe0ec"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#9a295c" flood-opacity=".18"/>
    </filter>
  </defs>

  <rect width="1080" height="1080" rx="0" fill="url(#bg)"/>

  <rect x="86" y="86" width="908" height="908" rx="54" fill="#ffffff" filter="url(#shadow)" opacity=".94"/>

  <text x="132" y="180" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="800" fill="#064750">MaryLouse Ofertas</text>

  <text x="132" y="292" font-family="Arial, Helvetica, sans-serif" font-size="88" font-weight="900" fill="#ef2473">{svg_escape(emoji)} {svg_escape(label)}</text>

  <text x="132" y="370" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="800" fill="#1f1720">Achadinhos e descontos atualizados</text>

  <rect x="132" y="430" width="816" height="250" rx="38" fill="#fff4f8" stroke="#f0d7df"/>

  <text x="174" y="500" font-family="Arial, Helvetica, sans-serif" font-size="36" font-weight="900" fill="#ef2473">{svg_escape(discount)}</text>
  <text x="174" y="570" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="900" fill="#1f1720">{svg_escape(offer_title)}</text>
  <text x="174" y="638" font-family="Arial, Helvetica, sans-serif" font-size="44" font-weight="900" fill="#08a64b">{svg_escape(price)}</text>

  <text x="132" y="760" font-family="Arial, Helvetica, sans-serif" font-size="36" font-weight="800" fill="#6e5e67">{count} oferta(s) nesta categoria hoje</text>

  <rect x="132" y="820" width="560" height="86" rx="43" fill="#ef2473"/>
  <text x="178" y="876" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="900" fill="#ffffff">Ver ofertas agora</text>

  <text x="132" y="956" font-family="Arial, Helvetica, sans-serif" font-size="28" font-weight="700" fill="#6e5e67">marylouse-ofertas.vercel.app</text>
</svg>
'''

    path = CARDS_DIR / f"{slug}.svg"
    path.write_text(svg, encoding="utf-8", newline="\n")
    return path


def write_social_posts(offers, counts):
    rows = []

    cat_map = category_by_name()

    for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        if count <= 0:
            continue

        cat = cat_map.get(category)

        if not cat:
            continue

        top = top_offers(offers, category, limit=1)
        top_offer = top[0] if top else None

        campaign = f"organic_{cat['slug']}"
        url = page_url_for_category(cat, "social", "organic", campaign)
        card_url = f"{SITE_URL}/growth/cards/{cat['slug']}.svg"

        title = f"{cat['emoji']} Ofertas de {cat['label']} atualizadas hoje"

        if top_offer:
            caption = (
                f"{cat['emoji']} Ofertas de {cat['label']} atualizadas hoje!\n\n"
                f"Destaque: {top_offer.get('title')}\n"
                f"Preço: {get_price(top_offer) or 'ver no site'}\n\n"
                f"Veja as ofertas antes que mudem:\n{url}"
            )
        else:
            caption = (
                f"{cat['emoji']} Ofertas de {cat['label']} atualizadas hoje!\n\n"
                f"Veja achadinhos e descontos selecionados pela MaryLouse:\n{url}"
            )

        hashtags = hashtags_for_category(category)

        for platform in ["Instagram", "Facebook", "Threads"]:
            rows.append({
                "platform": platform,
                "campaign": campaign,
                "category": cat["label"],
                "title": title,
                "caption": caption,
                "hashtags": hashtags,
                "url": url,
                "card_url": card_url,
            })

    out = OUTPUT_DIR / "social_posts.csv"

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["platform", "campaign", "category", "title", "caption", "hashtags", "url", "card_url"],
            delimiter=";"
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK: {out} | {len(rows)} posts")


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


def write_pinterest_pins(offers, counts):
    rows = []
    cat_map = category_by_name()

    for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        if count <= 0:
            continue

        cat = cat_map.get(category)

        if not cat:
            continue

        campaign = f"pinterest_{cat['slug']}"
        url = page_url_for_category(cat, "pinterest", "organic", campaign)
        card_url = f"{SITE_URL}/growth/cards/{cat['slug']}.svg"

        intents = SEO_INTENTS.get(category, [])

        title = f"{cat['emoji']} {cat['label']}: ofertas atualizadas hoje"

        description = (
            f"Veja ofertas de {cat['label']} selecionadas pela MaryLouse Ofertas. "
            f"Produtos atualizados, descontos e links de lojas parceiras. "
            f"{', '.join(intents[:3])}."
        )

        rows.append({
            "board": "MaryLouse Ofertas",
            "title": title,
            "description": description,
            "link": url,
            "image": card_url,
            "keywords": ", ".join(intents),
        })

    out = OUTPUT_DIR / "pinterest_pins.csv"

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["board", "title", "description", "link", "image", "keywords"],
            delimiter=";"
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK: {out} | {len(rows)} pins")


def write_telegram_digest(offers, counts):
    top = top_offers(offers, limit=8)

    lines = []
    lines.append("🔥 Top ofertas MaryLouse de hoje")
    lines.append("")
    lines.append("Ofertas selecionadas automaticamente por desconto, recência e intenção de compra.")
    lines.append("")

    for i, offer in enumerate(top, start=1):
        category = offer.get("_category") or "Oferta"
        title = short(offer.get("title"), 78)
        price = get_price(offer) or "ver preço"
        url = offer_url(offer)

        lines.append(f"{i}. {title}")
        lines.append(f"   {category} | {price}")
        lines.append(f"   {url}")
        lines.append("")

    lines.append("🧭 Ver todas as categorias:")
    lines.append(f"{SITE_URL}/?utm_source=telegram&utm_medium=organic&utm_campaign=digest_diario#categorias")
    lines.append("")
    lines.append("Aviso: podemos receber comissão por compras feitas pelos links.")

    out = OUTPUT_DIR / "telegram_digest.txt"
    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8", newline="\n")

    print(f"OK: {out}")


def write_daily_plan(offers, counts):
    cat_map = category_by_name()
    ranked_categories = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    top_global = top_offers(offers, limit=10)

    lines = []
    lines.append("# Plano Diário de Divulgação Orgânica — MaryLouse Ofertas")
    lines.append("")
    lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append("")
    lines.append("## Objetivo do dia")
    lines.append("")
    lines.append("Gerar tráfego gratuito para páginas de categoria, aumentar cliques em ofertas e atrair novos inscritos para o Telegram.")
    lines.append("")
    lines.append("## Categorias com mais ofertas hoje")
    lines.append("")

    for category, count in ranked_categories[:10]:
        cat = cat_map.get(category)
        if not cat:
            continue
        url = page_url_for_category(cat, "organic_report", "organic", f"categoria_{cat['slug']}")
        lines.append(f"- {cat['emoji']} **{cat['label']}**: {count} oferta(s) — {url}")

    lines.append("")
    lines.append("## Top ofertas para destacar")
    lines.append("")

    for i, offer in enumerate(top_global, start=1):
        category = offer.get("_category") or "Oferta"
        marketplace = marketplace_label(offer.get("marketplace"))
        price = get_price(offer) or "ver preço"
        discount = discount_label(offer)
        url = offer_url(offer)
        lines.append(f"{i}. **{short(offer.get('title'), 100)}**")
        lines.append(f"   - Categoria: {category}")
        lines.append(f"   - Loja: {marketplace}")
        lines.append(f"   - Preço: {price}")
        lines.append(f"   - Desconto: {discount}")
        lines.append(f"   - Link: {url}")
        lines.append("")

    lines.append("## Ações gratuitas recomendadas")
    lines.append("")
    lines.append("1. Publicar 3 pins no Pinterest usando `growth/output/pinterest_pins.csv`.")
    lines.append("2. Publicar 2 posts sociais usando `growth/output/social_posts.csv`.")
    lines.append("3. Enviar ou adaptar o resumo de `growth/output/telegram_digest.txt` no Telegram.")
    lines.append("4. Conferir no GA4 quais categorias receberam mais cliques.")
    lines.append("5. Reforçar manualmente as categorias com maior intenção de compra: Bebê, Casa e Cozinha, Celulares, Supermercados e Beleza.")
    lines.append("")
    lines.append("## Arquivos gerados")
    lines.append("")
    lines.append("- `growth/output/social_posts.csv`")
    lines.append("- `growth/output/pinterest_pins.csv`")
    lines.append("- `growth/output/telegram_digest.txt`")
    lines.append("- `growth/cards/*.svg`")
    lines.append("- `feed.xml`")

    out = OUTPUT_DIR / "daily_growth_plan.md"
    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8", newline="\n")

    print(f"OK: {out}")


def write_feed(offers):
    top = top_offers(offers, limit=50)

    items = []

    cat_map = category_by_name()

    for offer in top:
        category = offer.get("_category") or "Outros"
        cat = cat_map.get(category, {"slug": "outros"})
        page_link = f"{SITE_URL}/ofertas-{cat['slug']}.html"
        title = offer.get("title") or "Oferta MaryLouse"
        desc = f"{category} | {marketplace_label(offer.get('marketplace'))} | {get_price(offer) or 'ver preço'}"

        items.append(f"""
    <item>
      <title>{xml_escape.escape(title)}</title>
      <link>{xml_escape.escape(page_link)}</link>
      <description>{xml_escape.escape(desc)}</description>
      <guid>{xml_escape.escape(page_link + '#' + normalize(title)[:60])}</guid>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>MaryLouse Ofertas</title>
    <link>{SITE_URL}/</link>
    <description>Ofertas, achadinhos e descontos atualizados automaticamente.</description>
    <language>pt-BR</language>
    <lastBuildDate>{datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
{''.join(items)}
  </channel>
</rss>
"""

    Path("feed.xml").write_text(rss, encoding="utf-8", newline="\n")
    print("OK: feed.xml")


def main():
    ensure_dirs()

    offers = load_offers()

    counts = {}

    for offer in offers:
        category = offer.get("_category") or "Outros"
        counts[category] = counts.get(category, 0) + 1

    cat_map = category_by_name()

    for category, count in counts.items():
        cat = cat_map.get(category)
        if not cat:
            continue

        top = top_offers(offers, category, limit=1)
        top_offer = top[0] if top else None
        write_svg_card(cat, count, top_offer)

    write_social_posts(offers, counts)
    write_pinterest_pins(offers, counts)
    write_telegram_digest(offers, counts)
    write_daily_plan(offers, counts)
    write_feed(offers)

    print()
    print("Organic Growth Agent concluído.")


if __name__ == "__main__":
    main()
