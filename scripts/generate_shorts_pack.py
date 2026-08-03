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


def safe_label(value):
    # Evita emojis no texto renderizado pelo Pillow para não aparecer quadradinho.
    text = str(value or "")
    for emoji in ["🍼", "🍳", "💄", "📱", "🛒", "🔥", "❤️", "👗", "👟", "🐶", "🎧", "💻"]:
        text = text.replace(emoji, "")
    return text.strip()


def draw_wrapped(draw, text, x, y, max_chars, max_lines, font_obj, fill, line_gap=10):
    lines = wrap_lines(text, max_chars=max_chars, max_lines=max_lines)
    current_y = y

    for line in lines:
        draw.text((x, current_y), line, font=font_obj, fill=fill)
        current_y += font_obj.size + line_gap

    return current_y


def draw_centered_text(draw, text, y, font_obj, fill, x1=0, x2=W):
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    tw = bbox[2] - bbox[0]
    x = x1 + ((x2 - x1) - tw) // 2
    draw.text((x, y), text, font=font_obj, fill=fill)


def slide_intro(config):
    img = gradient_bg(config["theme"])
    draw = ImageDraw.Draw(img)

    # Card central
    rounded(draw, (60, 90, 1020, 1830), 64, "#ffffff")

    logo = load_logo()

    if logo:
        logo.thumbnail((170, 170), Image.LANCZOS)
        img.alpha_composite(logo, ((W - logo.width) // 2, 230))

    draw_centered_text(draw, "MaryLouse Ofertas", 455, font(58, True), "#064750")
    draw_centered_text(draw, "Achadinhos atualizados", 530, font(34, True), "#ef2473")

    category = safe_label(config["label"])

    # Pílula de categoria
    rounded(draw, (150, 680, 930, 780), 50, config["theme"])
    draw_centered_text(draw, category, 705, font(40, True), "#ffffff", 150, 930)

    draw_wrapped(
        draw,
        "Ofertas selecionadas para economizar hoje",
        120,
        920,
        max_chars=24,
        max_lines=3,
        font_obj=font(70, True),
        fill="#1f1720",
        line_gap=16,
    )

    rounded(draw, (120, 1310, 850, 1430), 60, "#08a64b")
    draw.text((175, 1348), "Veja até o final", font=font(46, True), fill="#ffffff")

    draw.text((120, 1610), "Preços podem mudar a qualquer momento", font=font(29, True), fill="#6e5e67")
    draw.text((120, 1670), "marylouse-ofertas.vercel.app", font=font(32, True), fill="#064750")

    return img


def slide_product(config, offer, index):
    img = gradient_bg(config["theme"])
    draw = ImageDraw.Draw(img)

    theme = config["theme"]
    category = safe_label(config["label"])
    store = marketplace(offer)
    disc = discount_label(offer)
    current_price = price(offer)
    previous_price = old_price(offer)

    # Card principal
    rounded(draw, (50, 55, 1030, 1845), 58, "#ffffff")

    # Header
    logo = load_logo()

    if logo:
        logo.thumbnail((74, 74), Image.LANCZOS)
        img.alpha_composite(logo, (85, 85))

    draw.text((175, 88), "MaryLouse Ofertas", font=font(32, True), fill="#064750")
    draw.text((175, 130), "Oferta selecionada", font=font(22, True), fill="#ef2473")

    # Categoria no topo direito
    rounded(draw, (610, 82, 975, 142), 30, "#fff4f8", "#f0d7df", 2)
    draw_centered_text(draw, category[:22], 98, font(24, True), theme, 610, 975)

    # Bloco da imagem
    rounded(draw, (85, 210, 995, 850), 46, "#fff7fb", "#f0d7df", 2)

    product_img = load_image(image_url(offer))

    if product_img:
        paste_contain(img, product_img, (125, 250, 830, 560))
    else:
        logo = load_logo()
        if logo:
            paste_contain(img, logo, (125, 250, 830, 560))

    # Badge desconto
    rounded(draw, (120, 245, 370, 315), 35, "#ffb000")
    draw_centered_text(draw, disc, 264, font(28, True), "#221900", 120, 370)

    # Loja
    rounded(draw, (700, 245, 950, 315), 35, "#ffffff")
    draw_centered_text(draw, store[:16], 264, font(26, True), "#ef2473", 700, 950)

    # Bloco texto
    rounded(draw, (85, 895, 995, 1545), 46, "#ffffff", "#f0d7df", 2)

    draw.text((120, 945), f"Oferta {index}", font=font(34, True), fill=theme)

    y = draw_wrapped(
        draw,
        offer.get("title") or "Oferta encontrada",
        120,
        1010,
        max_chars=28,
        max_lines=4,
        font_obj=font(50, True),
        fill="#1f1720",
        line_gap=10,
    )

    # Preço
    price_y = 1290

    if previous_price:
        draw.text((120, price_y), f"De: {previous_price}", font=font(31, True), fill="#6e5e67")
        price_y += 52

    draw.text((120, price_y), "Por apenas", font=font(31, True), fill="#6e5e67")
    draw.text((120, price_y + 56), current_price, font=font(76, True), fill="#08a64b")

    # CTA
    rounded(draw, (120, 1610, 820, 1725), 58, "#08a64b")
    draw.text((175, 1648), "Veja no site", font=font(46, True), fill="#ffffff")

    draw.text((120, 1780), "Link na bio / MaryLouse Ofertas", font=font(29, True), fill="#6e5e67")

    return img


def slide_cta(config):
    img = gradient_bg(config["theme"])
    draw = ImageDraw.Draw(img)

    rounded(draw, (60, 90, 1020, 1830), 64, "#ffffff")

    logo = load_logo()

    if logo:
        logo.thumbnail((180, 180), Image.LANCZOS)
        img.alpha_composite(logo, ((W - logo.width) // 2, 230))

    draw_centered_text(draw, "Gostou das ofertas?", 500, font(62, True), "#1f1720")
    draw_centered_text(draw, "Veja mais achadinhos", 600, font(60, True), config["theme"])
    draw_centered_text(draw, "atualizados no site", 685, font(60, True), "#1f1720")

    rounded(draw, (120, 980, 960, 1110), 65, config["theme"])
    draw_centered_text(draw, "MaryLouse Ofertas", 1020, font(48, True), "#ffffff", 120, 960)

    draw_wrapped(
        draw,
        config["cta"],
        120,
        1250,
        max_chars=28,
        max_lines=2,
        font_obj=font(42, True),
        fill="#6e5e67",
        line_gap=10,
    )

    draw.text((120, 1460), "Preços e disponibilidade podem mudar.", font=font(30, True), fill="#6e5e67")
    draw.text((120, 1520), "Podemos receber comissão pelos links.", font=font(30, True), fill="#6e5e67")

    draw.text((120, 1690), "marylouse-ofertas.vercel.app", font=font(36, True), fill="#064750")

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
