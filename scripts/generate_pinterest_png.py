from pathlib import Path
from io import BytesIO
from urllib.parse import urlencode
import html
import json
import re
import unicodedata
import urllib.request

from PIL import Image, ImageDraw, ImageFont, ImageOps


SITE_URL = "https://marylouse-ofertas.vercel.app"

OFFERS_PATH = Path("data/offers.json")
OUT_DIR = Path("growth/pinterest")
LOGO_PATH = Path("assets/logo.png")

W = 1000
H = 1500


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
    "Sapatos Femininos": "Calçados",
    "Sapatos Masculinos": "Calçados",
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
        or ""
    )


def image_url(offer):
    return (
        offer.get("image_url")
        or offer.get("image")
        or offer.get("thumbnail")
        or ""
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


def discount(offer):
    try:
        value = float(offer.get("discount_percent") or 0)
    except Exception:
        value = 0

    if value > 0:
        return f"{value:.0f}% OFF"

    return "Oferta"


def short(value, limit=92):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + "…"


def score_offer(offer):
    score = 0

    try:
        d = float(offer.get("discount_percent") or 0)
    except Exception:
        d = 0

    if d >= 60:
        score += 40
    elif d >= 40:
        score += 28
    elif d >= 20:
        score += 16

    if price(offer):
        score += 10

    title = normalize(offer.get("title") or "")

    hot = [
        "fralda", "pampers", "air fryer", "smartphone", "celular", "notebook",
        "perfume", "barbeador", "racao", "panela", "secador", "chapinha"
    ]

    if any(t in title for t in hot):
        score += 20

    return score


def font(size, bold=False):
    candidates = []

    if bold:
        candidates += [
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates += [
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass

    return ImageFont.load_default()


def rounded_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def paste_contain(base, img, box):
    x, y, w, h = box

    img = img.convert("RGBA")
    img.thumbnail((w, h), Image.LANCZOS)

    px = x + (w - img.width) // 2
    py = y + (h - img.height) // 2

    base.alpha_composite(img, (px, py))


def load_image_from_url(url):
    if not url:
        return None

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()

        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception as exc:
        print(f"AVISO: falha carregando imagem {url}: {exc}")
        return None


def load_logo():
    if LOGO_PATH.exists():
        try:
            return Image.open(LOGO_PATH).convert("RGBA")
        except Exception:
            return None
    return None


def wrap_text(text, max_chars=28, max_lines=3):
    words = str(text or "").split()
    lines = []
    current = ""

    for word in words:
        candidate = (current + " " + word).strip()

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

        if len(lines) >= max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".,;: ") + "…"

    return lines


def create_gradient():
    img = Image.new("RGB", (W, H), "#fff4f8")
    px = img.load()

    top = (255, 242, 232)
    mid = (255, 247, 251)
    bottom = (255, 216, 232)

    for y in range(H):
        ratio = y / H

        if ratio < 0.5:
            r = ratio / 0.5
            c = tuple(int(top[i] * (1 - r) + mid[i] * r) for i in range(3))
        else:
            r = (ratio - 0.5) / 0.5
            c = tuple(int(mid[i] * (1 - r) + bottom[i] * r) for i in range(3))

        for x in range(W):
            px[x, y] = c

    return img.convert("RGBA")


def create_card(cat, offers):
    category = cat["category"]

    candidates = [o for o in offers if o.get("_category") == category]
    candidates.sort(key=score_offer, reverse=True)

    top = candidates[0] if candidates else None

    count = len(candidates)
    title = short(top.get("title"), 92) if top else f"Ofertas de {cat['label']} atualizadas hoje"
    price_text = price(top) if top else ""
    discount_text = discount(top) if top else "Ofertas"
    store_text = marketplace(top) if top else "MaryLouse"

    base = create_gradient()
    draw = ImageDraw.Draw(base)

    # Card principal
    rounded_rect(draw, (54, 54, 946, 1446), 58, "#ffffff", None)

    # Header
    logo = load_logo()
    if logo:
        logo.thumbnail((82, 82), Image.LANCZOS)
        base.alpha_composite(logo, (84, 84))

    draw.text((180, 92), "MaryLouse Ofertas", font=font(38, True), fill="#064750")
    draw.text((180, 138), "Achadinhos e descontos selecionados", font=font(22, True), fill="#ef2473")

    # Imagem do produto
    image_box = (84, 230, 832, 560)
    rounded_rect(draw, (84, 230, 916, 790), 42, "#fff4f8", "#f0d7df", 2)

    product_img = load_image_from_url(image_url(top) if top else "")

    if product_img:
        paste_contain(base, product_img, image_box)
    elif logo:
        paste_contain(base, logo, image_box)

    # Badges
    rounded_rect(draw, (112, 260, 340, 328), 34, "#ffb000")
    draw.text((142, 278), discount_text, font=font(28, True), fill="#221900")

    rounded_rect(draw, (670, 260, 888, 328), 34, "#ffffff")
    draw.text((708, 278), store_text[:14], font=font(27, True), fill="#ef2473")

    # Bloco texto
    rounded_rect(draw, (84, 835, 916, 1348), 42, "#ffffff", "#f0d7df", 2)

    draw.text((110, 900), f"{cat['emoji']} {cat['label']}", font=font(34, True), fill="#ef2473")

    y = 970

    for line in wrap_text(title, 30, 3):
        draw.text((110, y), line, font=font(42, True), fill="#1f1720")
        y += 56

    if price_text:
        draw.text((110, 1180), "Por apenas", font=font(30, True), fill="#6e5e67")
        draw.text((110, 1242), price_text, font=font(72, True), fill="#08a64b")
    else:
        draw.text((110, 1230), "Ver oferta no marketplace", font=font(42, True), fill="#08a64b")

    draw.text((110, 1330), f"{count} oferta(s) nesta categoria hoje", font=font(24, True), fill="#6e5e67")

    # Botão
    rounded_rect(draw, (110, 1374, 720, 1454), 40, "#08a64b")
    draw.text((160, 1396), "Comprar agora", font=font(34, True), fill="#ffffff")

    out = OUT_DIR / f"{cat['slug']}.png"
    base.convert("RGB").save(out, "PNG", optimize=True)

    print(f"OK: {out} | {count} oferta(s)")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        raise SystemExit("data/offers.json não é lista.")

    for offer in offers:
        offer["_category"] = canonical_category(offer)

    for cat in CATEGORY_DEFS:
        create_card(cat, offers)

    print("Cards PNG para Pinterest gerados.")


if __name__ == "__main__":
    main()
