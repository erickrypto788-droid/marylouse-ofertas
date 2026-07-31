from pathlib import Path
from io import BytesIO
from datetime import datetime
import csv
import json
import re
import textwrap
import unicodedata
import urllib.request

from PIL import Image, ImageDraw, ImageFont, ImageFilter


SITE_URL = "https://marylouse-ofertas.vercel.app"

OFFERS_PATH = Path("data/offers.json")
OUT_DIR = Path("growth/shorts")
SLIDES_DIR = OUT_DIR / "slides"
LOGO_PATH = Path("assets/logo.png")

W = 1080
H = 1920


CATEGORY_CONFIG = [
    {
        "key": "mae_bebe",
        "category": "Mãe e Bebê",
        "label": "Mamãe e Bebê",
        "emoji": "🍼",
        "theme": "#ef2473",
        "cta": "Veja ofertas para bebê no site",
        "url": f"{SITE_URL}/ofertas-mae-bebe.html",
    },
    {
        "key": "casa_cozinha",
        "category": "Casa e Cozinha",
        "label": "Casa e Cozinha",
        "emoji": "🍳",
        "theme": "#ef7d24",
        "cta": "Veja achadinhos de casa no site",
        "url": f"{SITE_URL}/ofertas-casa-cozinha.html",
    },
    {
        "key": "beleza",
        "category": "Beleza",
        "label": "Beleza e Cuidados",
        "emoji": "💄",
        "theme": "#cf1d5f",
        "cta": "Veja ofertas de beleza no site",
        "url": f"{SITE_URL}/ofertas-beleza.html",
    },
    {
        "key": "celulares",
        "category": "Celulares",
        "label": "Celulares e Tecnologia",
        "emoji": "📱",
        "theme": "#1279d6",
        "cta": "Veja ofertas de tecnologia no site",
        "url": f"{SITE_URL}/ofertas-celulares.html",
    },
    {
        "key": "supermercados",
        "category": "Supermercados",
        "label": "Supermercados",
        "emoji": "🛒",
        "theme": "#08a64b",
        "cta": "Veja ofertas de mercado no site",
        "url": f"{SITE_URL}/ofertas-supermercados.html",
    },
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

    if any(t in text for t in ["air fryer", "panela", "liquidificador", "cafeteira", "cozinha", "rack para tv", "painel para tv"]):
        return "Casa e Cozinha"

    if any(t in text for t in ["barbeador", "perfume", "secador", "chapinha", "escova secadora", "maquiagem", "shampoo"]):
        return "Beleza"

    if any(t in text for t in ["papel higienico", "detergente", "amaciante", "sabao em po", "sabonete", "creme dental", "arroz", "feijao", "azeite"]):
        return "Supermercados"

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


def discount_number(offer):
    try:
        return float(offer.get("discount_percent") or 0)
    except Exception:
        return 0.0


def discount_label(offer):
    d = discount_number(offer)

    if d > 0:
        return f"{d:.0f}% OFF"

    return "OFERTA"


def offer_url(offer):
    return (
        offer.get("affiliate_url")
        or offer.get("url")
        or offer.get("link")
        or offer.get("product_url")
        or "#"
    )


def score_offer(offer):
    score = 0

    d = discount_number(offer)

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
        "fralda", "pampers", "huggies", "mamypoko", "air fryer", "panela",
        "smartphone", "celular", "xiaomi", "samsung", "perfume", "barbeador",
        "secador", "chapinha", "papel higienico"
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


def load_logo():
    if LOGO_PATH.exists():
        try:
            return Image.open(LOGO_PATH).convert("RGBA")
        except Exception:
            return None
    return None


def load_image(url):
    if not url:
        return None

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()

        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception as exc:
        print(f"AVISO: falha carregando imagem: {exc}")
        return None


def gradient_bg(theme="#ef2473"):
    base = Image.new("RGB", (W, H), "#fff4f8")
    px = base.load()

    top = (255, 242, 232)
    mid = (255, 247, 251)
    bottom = tuple(int(theme.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

    bottom = tuple(int(bottom[i] * 0.22 + 255 * 0.78) for i in range(3))

    for y in range(H):
        r = y / H

        if r < 0.55:
            t = r / 0.55
            c = tuple(int(top[i] * (1 - t) + mid[i] * t) for i in range(3))
        else:
            t = (r - 0.55) / 0.45
            c = tuple(int(mid[i] * (1 - t) + bottom[i] * t) for i in range(3))

        for x in range(W):
            px[x, y] = c

    return base.convert("RGBA")


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def paste_contain(base, img, box):
    x, y, w, h = box
    img = img.convert("RGBA")
    img.thumbnail((w, h), Image.LANCZOS)
    px = x + (w - img.width) // 2
    py = y + (h - img.height) // 2
    base.alpha_composite(img, (px, py))


def wrap_lines(text, max_chars=24, max_lines=3):
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

    return lines or ["Oferta encontrada"]


def slide_intro(config):
    img = gradient_bg(config["theme"])
    draw = ImageDraw.Draw(img)

    logo = load_logo()

    if logo:
        logo.thumbnail((170, 170), Image.LANCZOS)
        img.alpha_composite(logo, ((W - logo.width) // 2, 210))

    draw.text((90, 470), "MaryLouse Ofertas", font=font(56, True), fill="#064750")
    draw.text((90, 570), f"{config['emoji']} {config['label']}", font=font(72, True), fill=config["theme"])

    lines = [
        "Achadinhos e descontos",
        "atualizados hoje",
    ]

    y = 760

    for line in lines:
        draw.text((90, y), line, font=font(68, True), fill="#1f1720")
        y += 82

    rounded(draw, (90, 1120, 860, 1240), 60, config["theme"])
    draw.text((135, 1155), "Veja até o final", font=font(44, True), fill="#ffffff")

    draw.text((90, 1625), "Preços podem mudar a qualquer momento", font=font(28, True), fill="#6e5e67")
    draw.text((90, 1680), "marylouse-ofertas.vercel.app", font=font(30, True), fill="#6e5e67")

    return img


def slide_product(config, offer, index):
    img = gradient_bg(config["theme"])
    draw = ImageDraw.Draw(img)

    # Card branco
    rounded(draw, (55, 65, 1025, 1815), 56, "#ffffff")

    draw.text((95, 105), f"{config['emoji']} Oferta {index}", font=font(42, True), fill=config["theme"])
    draw.text((95, 160), marketplace(offer), font=font(32, True), fill="#6e5e67")

    # imagem
    rounded(draw, (95, 245, 985, 850), 42, "#fff4f8", "#f0d7df", 2)

    product_img = load_image(image_url(offer))
    logo = load_logo()

    if product_img:
        paste_contain(img, product_img, (115, 265, 850, 565))
    elif logo:
        paste_contain(img, logo, (115, 265, 850, 565))

    # badge desconto
    rounded(draw, (125, 280, 370, 352), 36, "#ffb000")
    draw.text((158, 300), discount_label(offer), font=font(30, True), fill="#221900")

    # título
    y = 930

    for line in wrap_lines(offer.get("title"), 28, 4):
        draw.text((95, y), line, font=font(50, True), fill="#1f1720")
        y += 62

    old = old_price(offer)

    if old:
        draw.text((95, 1240), f"De: {old}", font=font(34, True), fill="#6e5e67")

    draw.text((95, 1315), "Por apenas", font=font(34, True), fill="#6e5e67")
    draw.text((95, 1385), price(offer), font=font(82, True), fill="#08a64b")

    rounded(draw, (95, 1580, 760, 1690), 55, config["theme"])
    draw.text((145, 1613), "Veja no site", font=font(46, True), fill="#ffffff")

    draw.text((95, 1750), "Link na bio / MaryLouse Ofertas", font=font(28, True), fill="#6e5e67")

    return img


def slide_cta(config):
    img = gradient_bg(config["theme"])
    draw = ImageDraw.Draw(img)

    logo = load_logo()

    if logo:
        logo.thumbnail((190, 190), Image.LANCZOS)
        img.alpha_composite(logo, ((W - logo.width) // 2, 220))

    draw.text((90, 520), "Gostou das ofertas?", font=font(66, True), fill="#1f1720")
    draw.text((90, 630), "Veja mais achadinhos", font=font(62, True), fill=config["theme"])
    draw.text((90, 720), "atualizados no site", font=font(62, True), fill="#1f1720")

    rounded(draw, (90, 1010, 900, 1140), 65, config["theme"])
    draw.text((140, 1050), "MaryLouse Ofertas", font=font(48, True), fill="#ffffff")

    draw.text((90, 1260), config["cta"], font=font(42, True), fill="#6e5e67")
    draw.text((90, 1360), "Preços e disponibilidade podem mudar.", font=font(30, True), fill="#6e5e67")
    draw.text((90, 1420), "Podemos receber comissão pelos links.", font=font(30, True), fill="#6e5e67")

    draw.text((90, 1680), "marylouse-ofertas.vercel.app", font=font(34, True), fill="#064750")

    return img


def load_offers():
    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        raise SystemExit("data/offers.json não é lista.")

    for offer in offers:
        offer["_category"] = canonical_category(offer)
        offer["_growth_score"] = score_offer(offer)

    return offers


def top_by_category(offers, category, limit=3):
    pool = [offer for offer in offers if offer.get("_category") == category]
    pool.sort(key=lambda o: o.get("_growth_score") or 0, reverse=True)
    return pool[:limit]


def generate_pack(config, offers):
    folder = SLIDES_DIR / config["key"]
    folder.mkdir(parents=True, exist_ok=True)

    selected = top_by_category(offers, config["category"], limit=3)

    if not selected:
        return None

    slides = []

    intro = slide_intro(config)
    intro_path = folder / "01_intro.png"
    intro.save(intro_path, "PNG", optimize=True)
    slides.append(intro_path)

    for idx, offer in enumerate(selected, start=1):
        slide = slide_product(config, offer, idx)
        path = folder / f"0{idx + 1}_produto_{idx}.png"
        slide.save(path, "PNG", optimize=True)
        slides.append(path)

    cta = slide_cta(config)
    cta_path = folder / "05_cta.png"
    cta.save(cta_path, "PNG", optimize=True)
    slides.append(cta_path)

    title = f"{config['emoji']} Ofertas de {config['label']} atualizadas hoje"

    description = (
        f"Ofertas de {config['label']} selecionadas pela MaryLouse. "
        f"Preços podem mudar. Veja no site. #MaryLouseOfertas #Ofertas #Achadinhos"
    )

    return {
        "key": config["key"],
        "category": config["label"],
        "title": title,
        "description": description,
        "url": config["url"],
        "slides": [str(p).replace('\\\\', '/') for p in slides],
        "products": [offer.get("title") for offer in selected],
    }


def write_outputs(packs):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    md = []
    md.append("# Shorts Pack do Dia — MaryLouse Ofertas")
    md.append("")
    md.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    md.append("")
    md.append("## Como usar")
    md.append("")
    md.append("1. Abra CapCut, Canva ou Clipchamp.")
    md.append("2. Crie um vídeo vertical 9:16.")
    md.append("3. Importe os slides PNG da categoria escolhida.")
    md.append("4. Defina 2 a 4 segundos por slide.")
    md.append("5. Exporte como vídeo para TikTok, Shorts, Reels ou Status.")
    md.append("")
    md.append("---")
    md.append("")

    rows = []

    for pack in packs:
        md.append(f"## {pack['category']}")
        md.append("")
        md.append(f"**Título sugerido:** {pack['title']}")
        md.append("")
        md.append(f"**Descrição sugerida:** {pack['description']}")
        md.append("")
        md.append(f"**Link/CTA:** {pack['url']}")
        md.append("")
        md.append("**Slides:**")
        md.append("")

        for slide in pack["slides"]:
            md.append(f"- {slide}")

        md.append("")
        md.append("**Produtos usados:**")
        md.append("")

        for product in pack["products"]:
            md.append(f"- {product}")

        md.append("")
        md.append("---")
        md.append("")

        rows.append({
            "category": pack["category"],
            "title": pack["title"],
            "description": pack["description"],
            "url": pack["url"],
            "slides": " | ".join(pack["slides"]),
            "products": " | ".join(str(x) for x in pack["products"]),
        })

    (OUT_DIR / "shorts_today.md").write_text("\n".join(md).strip() + "\n", encoding="utf-8")

    with (OUT_DIR / "shorts_today.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["category", "title", "description", "url", "slides", "products"],
            delimiter=";"
        )
        writer.writeheader()
        writer.writerows(rows)

    print("OK: growth/shorts/shorts_today.md")
    print("OK: growth/shorts/shorts_today.csv")


def main():
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)

    offers = load_offers()

    packs = []

    for config in CATEGORY_CONFIG:
        pack = generate_pack(config, offers)

        if pack:
            packs.append(pack)

    write_outputs(packs)

    print(f"Shorts Pack gerado. Categorias: {len(packs)}")


if __name__ == "__main__":
    main()
