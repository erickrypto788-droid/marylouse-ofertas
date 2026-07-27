from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
import html
import json
import re
import unicodedata
import xml.sax.saxutils as xml_escape


SITE_URL = "https://marylouse-ofertas.vercel.app"

OFFERS_PATH = Path("data/offers.json")
CARDS_DIR = Path("growth/cards")

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

CATEGORY_SLUGS = {c["category"]: c["slug"] for c in CATEGORY_DEFS}


def esc(value):
    return html.escape(str(value or ""), quote=True)


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

    if raw in CATEGORY_SLUGS:
        return raw

    return "Outros"


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


def image(offer):
    return (
        offer.get("image_url")
        or offer.get("image")
        or offer.get("thumbnail")
        or f"{SITE_URL}/assets/logo.png"
    )


def affiliate_link(offer):
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


def discount(offer):
    try:
        value = float(offer.get("discount_percent") or 0)
    except Exception:
        value = 0

    if value > 0:
        return f"{value:.0f}% OFF"

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


def split_lines(value, max_chars=30, max_lines=3):
    words = str(value or "").replace("\n", " ").split()
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

    return lines or ["Ofertas atualizadas"]


def score_offer(offer):
    score = 0

    try:
        d = float(offer.get("discount_percent") or 0)
    except Exception:
        d = 0

    if d >= 50:
        score += 40
    elif d >= 30:
        score += 25
    elif d >= 15:
        score += 12

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


def page_url(cat):
    params = urlencode({
        "utm_source": "pinterest",
        "utm_medium": "organic",
        "utm_campaign": f"card_{cat['slug']}",
    })
    return f"{SITE_URL}/ofertas-{cat['slug']}.html?{params}"


def load_offers():
    if not OFFERS_PATH.exists():
        raise SystemExit("data/offers.json não encontrado.")

    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        raise SystemExit("data/offers.json não é lista.")

    for offer in offers:
        offer["_category"] = canonical_category(offer)
        offer["_created_ts"] = parse_ts(offer)

    offers.sort(key=lambda o: o.get("_created_ts") or 0, reverse=True)

    return offers


def generate_card(cat, offers):
    category = cat["category"]

    candidates = [o for o in offers if o.get("_category") == category]
    candidates.sort(key=score_offer, reverse=True)

    top = candidates[0] if candidates else None

    count = len(candidates)
    title = short(top.get("title"), 95) if top else f"Ofertas de {cat['label']} atualizadas hoje"
    img = image(top) if top else f"{SITE_URL}/assets/logo.png"
    price_text = price(top) if top else ""
    discount_text = discount(top) if top else "Ofertas"
    store_text = marketplace(top) if top else "MaryLouse"
    url = affiliate_link(top) if top else page_url(cat)

    title_nodes = []
    y = 970

    for line in split_lines(title, 32, 3):
        title_nodes.append(
            f'<text x="110" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="900" fill="#1f1720">{esc(line)}</text>'
        )
        y += 54

    if price_text:
        price_block = f"""
    <text x="110" y="1215" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="850" fill="#6e5e67">Por apenas</text>
    <text x="110" y="1290" font-family="Arial, Helvetica, sans-serif" font-size="76" font-weight="950" fill="#08a64b">{esc(price_text)}</text>
"""
    else:
        price_block = """
    <text x="110" y="1270" font-family="Arial, Helvetica, sans-serif" font-size="48" font-weight="900" fill="#08a64b">Ver oferta no marketplace</text>
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1620" viewBox="0 0 1080 1620">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fff2e8"/>
      <stop offset="45%" stop-color="#fff7fb"/>
      <stop offset="100%" stop-color="#ffd8e8"/>
    </linearGradient>

    <linearGradient id="btn" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#10b960"/>
      <stop offset="100%" stop-color="#07863b"/>
    </linearGradient>

    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="22" stdDeviation="20" flood-color="#9a295c" flood-opacity=".22"/>
    </filter>

    <clipPath id="imageClip">
      <rect x="90" y="245" width="900" height="560" rx="42"/>
    </clipPath>
  </defs>

  <a href="{esc(url)}" target="_top">
    <rect width="1080" height="1350" fill="url(#bg)"/>

    <rect x="58" y="56" width="964" height="1508" rx="58" fill="#ffffff" opacity=".97" filter="url(#shadow)"/>

    <image href="{SITE_URL}/assets/logo.png" x="90" y="88" width="92" height="92" preserveAspectRatio="xMidYMid slice"/>
    <text x="202" y="142" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="950" fill="#064750">MaryLouse Ofertas</text>
    <text x="202" y="180" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="800" fill="#ef2473">Achadinhos e descontos selecionados</text>

    <rect x="90" y="245" width="900" height="560" rx="42" fill="#fff4f8" stroke="#f0d7df"/>
    <image href="{esc(img)}" x="90" y="245" width="900" height="560" clip-path="url(#imageClip)" preserveAspectRatio="xMidYMid meet"/>

    <rect x="118" y="276" width="250" height="72" rx="36" fill="#ffb000"/>
    <text x="150" y="324" font-family="Arial, Helvetica, sans-serif" font-size="32" font-weight="950" fill="#221900">{esc(discount_text)}</text>

    <rect x="708" y="276" width="250" height="72" rx="36" fill="#ffffff" filter="url(#shadow)"/>
    <text x="748" y="324" font-family="Arial, Helvetica, sans-serif" font-size="32" font-weight="950" fill="#ef2473">{esc(store_text)}</text>

    <rect x="90" y="835" width="900" height="550" rx="42" fill="#ffffff" stroke="#f0d7df"/>

    <text x="110" y="915" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="950" fill="#ef2473">{esc(cat['emoji'])} {esc(cat['label'])}</text>

    {''.join(title_nodes)}

    {price_block}

    <text x="110" y="1388" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="800" fill="#6e5e67">{count} oferta(s) nesta categoria hoje</text>

    <rect x="110" y="1430" width="660" height="94" rx="43" fill="url(#btn)"/>
    <text x="165" y="1490" font-family="Arial, Helvetica, sans-serif" font-size="36" font-weight="950" fill="#ffffff">Comprar agora</text>
  </a>
</svg>
"""

    out = CARDS_DIR / f"{cat['slug']}.svg"
    out.write_text(svg, encoding="utf-8", newline="\n")
    print(f"OK: {out} | {count} oferta(s) | link={url}")


def write_rss_xsl():
    xsl = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <html>
      <head>
        <title>MaryLouse Ofertas — Feed RSS</title>
        <meta charset="UTF-8"/>
        <style>
          body { margin: 0; font-family: Arial, Helvetica, sans-serif; background: linear-gradient(180deg, #fff4f8, #ffffff); color: #1f1720; }
          .wrap { max-width: 980px; margin: 40px auto; padding: 0 20px; }
          .hero { background: #fff; border: 1px solid #f0d7df; border-radius: 28px; padding: 28px; box-shadow: 0 16px 35px rgba(154, 41, 92, .10); }
          h1 { margin: 0 0 8px; color: #064750; font-size: 36px; }
          p { color: #6e5e67; font-size: 17px; }
          .item { display: block; background: #fff; border: 1px solid #f0d7df; border-radius: 20px; padding: 18px; margin-top: 14px; text-decoration: none; color: inherit; }
          .item strong { color: #ef2473; font-size: 19px; }
          .btn { display: inline-block; margin-top: 18px; padding: 13px 18px; border-radius: 999px; background: #ef2473; color: #fff; text-decoration: none; font-weight: 900; }
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="hero">
            <h1>MaryLouse Ofertas — Feed RSS</h1>
            <p>Últimas ofertas publicadas automaticamente. Você também pode usar este link em leitores RSS.</p>
            <a class="btn" href="/">Voltar para o site</a>
          </div>
          <xsl:for-each select="rss/channel/item">
            <a class="item">
              <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
              <strong><xsl:value-of select="title"/></strong>
              <p><xsl:value-of select="description"/></p>
            </a>
          </xsl:for-each>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
"""
    Path("rss.xsl").write_text(xsl, encoding="utf-8", newline="\n")
    print("OK: rss.xsl")


def write_feed(offers):
    items = []

    for offer in offers[:50]:
        category = offer.get("_category") or "Outros"
        slug = CATEGORY_SLUGS.get(category, "outros")
        page = f"{SITE_URL}/ofertas-{slug}.html"
        title = offer.get("title") or "Oferta MaryLouse"
        desc = f"{category} | {marketplace(offer)} | {price(offer) or 'ver preço'}"

        items.append(f"""
    <item>
      <title>{xml_escape.escape(title)}</title>
      <link>{xml_escape.escape(page)}</link>
      <description>{xml_escape.escape(desc)}</description>
      <guid>{xml_escape.escape(page + '#' + normalize(title)[:60])}</guid>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/rss.xsl"?>
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


def write_feed_html(offers):
    cards = []

    for offer in offers[:42]:
        category = offer.get("_category") or "Outros"
        slug = CATEGORY_SLUGS.get(category, "outros")
        category_url = f"ofertas-{slug}.html"

        cards.append(f"""
        <article class="card">
          <a class="image" href="{esc(category_url)}">
            <img src="{esc(image(offer))}" alt="{esc(offer.get('title') or 'Oferta')}" loading="lazy"/>
          </a>
          <div class="body">
            <span class="cat">{esc(category)}</span>
            <h2>{esc(short(offer.get('title'), 88))}</h2>
            <p>{esc(marketplace(offer))} | {esc(price(offer))}</p>
            <a class="buy" href="{esc(category_url)}">Ver ofertas da categoria</a>
          </div>
        </article>
        """)

    page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Feed Visual de Ofertas | MaryLouse Ofertas</title>
  <meta name="description" content="Feed visual com as ofertas mais recentes da MaryLouse Ofertas."/>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: linear-gradient(180deg, #fff4f8, #ffffff); color: #1f1720; }}
    .header {{ background: rgba(255,255,255,.92); border-bottom: 1px solid #f0d7df; position: sticky; top: 0; z-index: 5; backdrop-filter: blur(12px); }}
    .header-inner {{ max-width: 1180px; margin: 0 auto; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }}
    .brand {{ display: flex; align-items: center; gap: 12px; text-decoration: none; color: #064750; font-size: 24px; font-weight: 950; }}
    .brand img {{ width: 54px; height: 54px; border-radius: 16px; }}
    .nav {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .nav a {{ text-decoration: none; padding: 11px 16px; border-radius: 999px; background: #fff; border: 1px solid #f0d7df; color: #6e5e67; font-weight: 900; }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 34px 20px; }}
    .hero {{ background: rgba(255,255,255,.9); border: 1px solid #f0d7df; border-radius: 32px; padding: 32px; box-shadow: 0 16px 35px rgba(154, 41, 92, .10); margin-bottom: 24px; }}
    h1 {{ margin: 0 0 10px; color: #064750; font-size: clamp(34px, 5vw, 56px); letter-spacing: -1.5px; }}
    .hero p {{ color: #6e5e67; font-size: 19px; line-height: 1.55; max-width: 850px; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .links a, .buy {{ display: inline-flex; align-items: center; justify-content: center; padding: 13px 17px; border-radius: 999px; background: #ef2473; color: #fff; text-decoration: none; font-weight: 950; }}
    .links a.secondary {{ background: #fff; color: #ef2473; border: 1px solid #f0d7df; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }}
    .card {{ background: #fff; border: 1px solid #f0d7df; border-radius: 26px; overflow: hidden; box-shadow: 0 14px 30px rgba(126, 34, 80, .10); }}
    .image {{ display: block; height: 245px; background: #fff; }}
    .image img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
    .body {{ padding: 17px; }}
    .cat {{ display: inline-block; margin-bottom: 8px; color: #ef2473; font-weight: 950; font-size: 13px; text-transform: uppercase; }}
    .card h2 {{ margin: 0 0 10px; font-size: 19px; line-height: 1.28; min-height: 74px; }}
    .card p {{ color: #6e5e67; font-weight: 850; }}
    .buy {{ width: 100%; border-radius: 16px; margin-top: 10px; background: linear-gradient(135deg, #10b960, #07863b); }}
    @media (max-width: 920px) {{ .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
    @media (max-width: 640px) {{ .header-inner {{ align-items: flex-start; flex-direction: column; }} .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header class="header">
    <div class="header-inner">
      <a class="brand" href="./index.html">
        <img src="./assets/logo.png" alt="MaryLouse Ofertas"/>
        <span>MaryLouse Ofertas</span>
      </a>
      <nav class="nav">
        <a href="./index.html#ofertas">🔥 Ofertas</a>
        <a href="./index.html#categorias">🧭 Categorias</a>
        <a href="https://t.me/dmaispromo" target="_blank" rel="noopener">📲 Telegram</a>
      </nav>
    </div>
  </header>
  <main class="wrap">
    <section class="hero">
      <h1>🔥 Feed visual de ofertas</h1>
      <p>As ofertas mais recentes da MaryLouse Ofertas em formato fácil de navegar. Use esta página para acompanhar os destaques e acessar as categorias atualizadas.</p>
      <div class="links">
        <a href="./index.html">Ver site completo</a>
        <a class="secondary" href="./feed.xml">Abrir RSS técnico</a>
        <a class="secondary" href="https://t.me/dmaispromo" target="_blank" rel="noopener">Entrar no Telegram</a>
      </div>
    </section>
    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""
    Path("feed.html").write_text(page, encoding="utf-8", newline="\n")
    print("OK: feed.html")


def main():
    CARDS_DIR.mkdir(parents=True, exist_ok=True)

    offers = load_offers()

    for cat in CATEGORY_DEFS:
        generate_card(cat, offers)

    write_rss_xsl()
    write_feed(offers)
    write_feed_html(offers)

    print("Organic publish concluído.")


if __name__ == "__main__":
    main()
