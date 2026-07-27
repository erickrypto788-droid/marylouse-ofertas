from pathlib import Path
from datetime import date, datetime, timezone
import html
import json
import re
import unicodedata


SITE_URL = "https://marylouse-ofertas.vercel.app"
SHOPEE_COUPONS_URL = "https://s.shopee.com.br/111NhMP4uM"

OFFERS_PATH = Path("data/offers.json")


SPECIAL_PAGES = [
    {
        "filename": "ofertas-amazon.html",
        "marketplace": "Amazon",
        "title": "Ofertas Amazon Hoje",
        "h1": "Ofertas Amazon atualizadas hoje",
        "description": "Veja achadinhos e ofertas Amazon selecionadas pela MaryLouse Ofertas. Produtos com preço, imagem e link de afiliado.",
        "keywords": "ofertas amazon hoje, promoções amazon, achadinhos amazon, amazon ofertas",
        "emoji": "🛒",
    },
    {
        "filename": "ofertas-shopee.html",
        "marketplace": "Shopee",
        "title": "Ofertas Shopee Hoje",
        "h1": "Ofertas Shopee atualizadas hoje",
        "description": "Confira achadinhos Shopee, promoções e produtos selecionados com links de afiliado e atualização frequente.",
        "keywords": "ofertas shopee hoje, achadinhos shopee, promoções shopee, shopee ofertas",
        "emoji": "🧡",
    },
    {
        "filename": "ofertas-mercado-livre.html",
        "marketplace": "Mercado Livre",
        "title": "Ofertas Mercado Livre Hoje",
        "h1": "Ofertas Mercado Livre atualizadas hoje",
        "description": "Veja ofertas do Mercado Livre selecionadas automaticamente, com descontos, categorias e links de afiliado.",
        "keywords": "ofertas mercado livre hoje, promoções mercado livre, mercado livre ofertas",
        "emoji": "💛",
    },
]


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


def image(offer):
    return (
        offer.get("image_url")
        or offer.get("image")
        or offer.get("thumbnail")
        or "assets/logo.png"
    )


def link(offer):
    return (
        offer.get("affiliate_url")
        or offer.get("url")
        or offer.get("link")
        or offer.get("product_url")
        or "#"
    )


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


def short(value, limit=110):
    text = str(value or "").strip()

    if len(text) <= limit:
        return text

    return text[:limit - 1].rstrip() + "…"


def load_offers():
    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        return []

    offers.sort(key=parse_ts, reverse=True)

    return offers


def offer_category(offer):
    raw = str(offer.get("category") or "Outros").strip()

    aliases = {
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

    raw = aliases.get(raw, raw)

    title = normalize(offer.get("title") or "")
    desc = normalize(offer.get("description") or "")
    text = f"{title} {desc} {normalize(raw)}"

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

    if any(t in text for t in ["hot wheels", "lego", "boneca", "boneco", "brinquedo", "jogo da forca"]):
        return "Brinquedos e Hobbies"

    if any(t in text for t in ["halter", "academia", "fitness", "bike spinning", "bicicleta", "whey", "creatina", "esteira", "corrida"]):
        return "Esportes"

    if any(t in text for t in ["caneta", "lapis", "caderno", "papelaria", "estojo", "material escolar"]):
        return "Papelaria"

    if any(t in text for t in ["furadeira", "parafusadeira", "ferramenta", "martelo", "trena", "alicate"]):
        return "Ferramentas"

    if any(t in text for t in [
        "vestido", "saia", "cropped", "blusa feminina", "camisa feminina",
        "camiseta feminina", "calca feminina", "calça feminina", "legging",
        "calca legging", "calça legging", "top feminino", "conjunto feminino",
        "moda feminina", "roupas femininas", "feminina", "mulher", "women",
        "body feminino", "short feminino", "shorts feminino"
    ]):
        return "Moda Feminina"

    if any(t in text for t in [
        "camiseta masculina", "camisa masculina", "calca masculina",
        "calça masculina", "bermuda masculina", "short masculino",
        "shorts masculino", "cueca", "moda masculina", "roupas masculinas",
        "masculina", "masculino", "homem", "men shirt", "men", "polo masculina"
    ]):
        return "Moda Masculina"

    if any(t in text for t in [
        "plus size", "moda plus size", "roupas plus size", "tamanho grande",
        "gg plus", "xg plus"
    ]):
        return "Moda Plus Size"

    if any(t in text for t in [
        "infantil", "menino", "menina", "crianca", "criança", "kids",
        "roupa infantil", "moda infantil", "bebê menino", "bebe menino",
        "bebê menina", "bebe menina"
    ]):
        return "Moda Infantil"

    return raw or "Outros"


def category_order():
    return [
        "Todos",
        "Supermercados",
        "Celulares",
        "Eletrônicos",
        "Informática",
        "Games",
        "Casa e Cozinha",
        "Eletrodomésticos",
        "Moda Feminina",
        "Moda Masculina",
        "Moda Plus Size",
        "Moda Infantil",
        "Calçados",
        "Bolsas",
        "Beleza",
        "Esportes",
        "Brinquedos e Hobbies",
        "Mãe e Bebê",
        "Pet",
        "Saúde",
        "Papelaria",
        "Ferramentas",
        "Outros",
    ]


def build_filters(offers):
    counts = {}

    for offer in offers:
        cat = offer_category(offer)
        counts[cat] = counts.get(cat, 0) + 1

    buttons = []

    total = len(offers)

    buttons.append(
        f'<button class="filter-btn active" type="button" data-category="Todos">✨ Todos <small>({total})</small></button>'
    )

    for cat in category_order():
        if cat == "Todos":
            continue

        count = counts.get(cat, 0)

        if count <= 0:
            continue

        buttons.append(
            f'<button class="filter-btn" type="button" data-category="{esc(cat)}">{esc(cat)} <small>({count})</small></button>'
        )

    return "\n".join(buttons)


def card(offer):
    title = offer.get("title") or "Oferta"
    url = link(offer)
    img = image(offer)
    mp = marketplace_label(offer.get("marketplace"))
    price_text = price(offer)
    old = old_price(offer)
    badge = discount(offer)
    cat = offer_category(offer)

    old_html = ""

    if old:
        old_html = f'<div class="old">De: <span>{esc(old)}</span></div>'
    else:
        old_html = '<div class="old">Oferta por tempo limitado</div>'

    return f"""
    <article class="card" data-category="{esc(cat)}">
      <a class="image" href="{esc(url)}" target="_blank" rel="nofollow sponsored noopener">
        <img src="{esc(img)}" alt="{esc(title)}" loading="lazy"/>
        <span class="badge">{esc(badge)}</span>
        <span class="store">{esc(mp)}</span>
      </a>

      <div class="body">
        <div class="cat">{esc(cat)}</div>
        <h2>{esc(short(title, 90))}</h2>
        <div class="pricebox">
          {old_html}
          <div class="price-line">
            <span>Por apenas</span>
            <strong>{esc(price_text)}</strong>
          </div>
        </div>
        <a class="buy" href="{esc(url)}" target="_blank" rel="nofollow sponsored noopener">🛒 Comprar agora</a>
      </div>
    </article>
    """


def layout(page, offers):
    page_url = f"{SITE_URL}/{page['filename']}"
    title = f"{page['title']} | MaryLouse Ofertas"
    description = page["description"]

    count = len(offers)
    cards_html = "\n".join(card(offer) for offer in offers)

    if not cards_html:
        cards_html = '<div class="empty">Nenhuma oferta disponível agora. Volte em breve.</div>'

    filters_html = build_filters(offers)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}"/>
  <meta name="keywords" content="{esc(page.get('keywords', ''))}"/>
  <meta name="robots" content="index, follow, max-image-preview:large"/>
  <link rel="canonical" href="{esc(page_url)}"/>
  <link rel="icon" type="image/svg+xml" href="./assets/favicon.svg"/>

  <meta property="og:type" content="website"/>
  <meta property="og:title" content="{esc(title)}"/>
  <meta property="og:description" content="{esc(description)}"/>
  <meta property="og:url" content="{esc(page_url)}"/>
  <meta property="og:image" content="{SITE_URL}/assets/logo.png"/>

  <style>
    :root {{
      --pink: #ef2473;
      --green: #08a64b;
      --ink: #1f1720;
      --muted: #6e5e67;
      --border: #f0d7df;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background:
        radial-gradient(circle at top left, #ffe0cf, transparent 34%),
        linear-gradient(180deg, #fff4f8, #ffffff);
      color: var(--ink);
    }}

    .header {{
      background: rgba(255,255,255,.92);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 5;
      backdrop-filter: blur(12px);
    }}

    .header-inner {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 14px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      color: #064750;
      text-decoration: none;
      font-weight: 950;
      font-size: 24px;
    }}

    .brand img {{
      width: 54px;
      height: 54px;
      border-radius: 16px;
    }}

    .nav {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .nav a {{
      text-decoration: none;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 11px 16px;
      background: #fff;
      color: var(--muted);
      font-weight: 900;
    }}

    .wrap {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 34px 20px;
    }}

    .hero {{
      background: rgba(255,255,255,.92);
      border: 1px solid var(--border);
      border-radius: 32px;
      padding: 32px;
      box-shadow: 0 16px 35px rgba(154, 41, 92, .10);
      margin-bottom: 24px;
    }}

    h1 {{
      margin: 0 0 10px;
      font-size: clamp(34px, 5vw, 56px);
      color: #064750;
      letter-spacing: -1.5px;
    }}

    .hero p {{
      color: var(--muted);
      font-size: 19px;
      line-height: 1.55;
      max-width: 850px;
    }}

    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}

    .btn {{
      text-decoration: none;
      background: var(--pink);
      color: #fff;
      padding: 13px 18px;
      border-radius: 999px;
      font-weight: 950;
      display: inline-flex;
    }}

    .btn.secondary {{
      background: #fff;
      color: var(--pink);
      border: 1px solid var(--border);
    }}

    .filters {{
      margin: 0 0 22px;
      padding: 22px;
      background: rgba(255,255,255,.9);
      border: 1px solid var(--border);
      border-radius: 28px;
      box-shadow: 0 12px 26px rgba(126, 34, 80, .08);
    }}

    .filters h2 {{
      margin: 0 0 12px;
      font-size: 24px;
    }}

    .filter-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}

    .filter-btn {{
      border: 1px solid var(--border);
      background: #fff;
      color: var(--muted);
      border-radius: 999px;
      padding: 11px 15px;
      font-weight: 950;
      cursor: pointer;
      font-size: 15px;
    }}

    .filter-btn.active {{
      background: var(--pink);
      color: #fff;
      border-color: var(--pink);
      box-shadow: 0 10px 20px rgba(239, 36, 115, .18);
    }}

    .result-note {{
      margin-top: 12px;
      color: var(--muted);
      font-weight: 800;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 20px;
    }}

    .card {{
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 26px;
      overflow: hidden;
      box-shadow: 0 14px 30px rgba(126, 34, 80, .10);
    }}

    .image {{
      display: block;
      position: relative;
      height: 250px;
      background: #fff;
    }}

    .image img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}

    .badge {{
      position: absolute;
      left: 14px;
      top: 14px;
      background: #ffb000;
      padding: 9px 12px;
      border-radius: 999px;
      font-weight: 950;
    }}

    .store {{
      position: absolute;
      right: 14px;
      top: 14px;
      background: #fff;
      color: var(--pink);
      padding: 9px 12px;
      border-radius: 999px;
      font-weight: 950;
      box-shadow: 0 8px 18px rgba(0,0,0,.12);
    }}

    .body {{
      padding: 17px;
    }}

    .cat {{
      color: var(--pink);
      font-size: 13px;
      font-weight: 950;
      text-transform: uppercase;
      margin-bottom: 8px;
    }}

    .card h2 {{
      margin: 0 0 12px;
      font-size: 20px;
      line-height: 1.25;
      min-height: 78px;
    }}

    .pricebox {{
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 12px;
      background: #fffafd;
      margin-bottom: 13px;
    }}

    .old {{
      color: var(--muted);
      font-size: 13px;
      font-weight: 850;
      margin-bottom: 7px;
    }}

    .old span {{
      text-decoration: line-through;
    }}

    .price-line {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 10px;
      color: var(--muted);
      font-weight: 900;
    }}

    .price-line strong {{
      color: var(--green);
      font-size: 25px;
      font-weight: 950;
      white-space: nowrap;
    }}

    .buy {{
      display: flex;
      justify-content: center;
      text-decoration: none;
      background: linear-gradient(135deg, #10b960, #07863b);
      color: #fff;
      border-radius: 16px;
      padding: 14px 16px;
      font-weight: 950;
    }}

    .empty {{
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px;
      text-align: center;
      color: var(--muted);
    }}

    @media (max-width: 920px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}

    @media (max-width: 640px) {{
      .header-inner {{
        align-items: flex-start;
        flex-direction: column;
      }}

      .grid {{ grid-template-columns: 1fr; }}
    }}
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
        <a href="./index.html#marketplaces">🛍️ Marketplaces</a>
        <a href="./cupons-shopee.html">🎟️ Cupons</a>
        <a href="./feed.html">📡 Feed</a>
        <a href="https://t.me/dmaispromo" target="_blank" rel="noopener">📲 Telegram</a>
      </nav>
    </div>
  </header>

  <main class="wrap">
    <section class="hero">
      <h1>{page['emoji']} {esc(page['h1'])}</h1>
      <p>{esc(description)}</p>
      <p><strong>{count}</strong> oferta(s) encontrada(s) agora.</p>

      <div class="actions">
        <a class="btn" href="#ofertas">Ver ofertas</a>
        <a class="btn secondary" href="./index.html#marketplaces">Voltar para marketplaces</a>
      </div>
    </section>

    <section class="filters">
      <h2>Filtrar por categoria</h2>
      <div class="filter-list">
        {filters_html}
      </div>
      <div class="result-note" id="resultNote">Exibindo todas as ofertas.</div>
    </section>

    <section id="ofertas" class="grid">
      {cards_html}
    </section>
  </main>

  <script>
    (function () {{
      const buttons = Array.from(document.querySelectorAll(".filter-btn"));
      const cards = Array.from(document.querySelectorAll(".card"));
      const note = document.getElementById("resultNote");

      function applyFilter(category) {{
        let visible = 0;

        cards.forEach(function (card) {{
          const cardCategory = card.getAttribute("data-category") || "Outros";
          const show = category === "Todos" || cardCategory === category;

          card.style.display = show ? "" : "none";

          if (show) visible++;
        }});

        buttons.forEach(function (btn) {{
          btn.classList.toggle("active", btn.getAttribute("data-category") === category);
        }});

        if (note) {{
          if (category === "Todos") {{
            note.textContent = "Exibindo todas as ofertas.";
          }} else {{
            note.textContent = "Exibindo " + visible + " oferta(s) em " + category + ".";
          }}
        }}
      }}

      buttons.forEach(function (btn) {{
        btn.addEventListener("click", function () {{
          applyFilter(btn.getAttribute("data-category") || "Todos");
        }});
      }});
    }})();
  </script>
</body>
</html>
"""

def cupons_shopee_page():
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Cupons Shopee Ativos Hoje | MaryLouse Ofertas</title>
  <meta name="description" content="Pegue cupons Shopee ativos hoje, frete grátis, descontos e ofertas extras antes de finalizar sua compra."/>
  <meta name="keywords" content="cupom shopee hoje, cupons shopee ativos, cupom shopee frete grátis, shopee cupom desconto"/>
  <meta name="robots" content="index, follow, max-image-preview:large"/>
  <link rel="canonical" href="{SITE_URL}/cupons-shopee.html"/>
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: linear-gradient(180deg, #fff4f8, #ffffff);
      color: #1f1720;
    }}

    .wrap {{
      max-width: 980px;
      margin: 0 auto;
      padding: 48px 20px;
    }}

    .card {{
      background: #fff;
      border: 1px solid #f0d7df;
      border-radius: 34px;
      padding: 38px;
      box-shadow: 0 16px 35px rgba(154, 41, 92, .10);
    }}

    h1 {{
      color: #064750;
      font-size: clamp(36px, 6vw, 64px);
      line-height: 1.02;
      margin: 0 0 18px;
    }}

    p {{
      color: #6e5e67;
      font-size: 20px;
      line-height: 1.55;
    }}

    ul {{
      color: #6e5e67;
      font-size: 19px;
      line-height: 1.8;
    }}

    .btn {{
      display: inline-flex;
      margin-top: 18px;
      padding: 16px 24px;
      border-radius: 999px;
      background: #ef2473;
      color: #fff;
      text-decoration: none;
      font-weight: 950;
      font-size: 20px;
    }}

    .secondary {{
      background: #fff;
      color: #ef2473;
      border: 1px solid #f0d7df;
      margin-left: 10px;
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="card">
      <h1>🎟️ Cupons Shopee ativos hoje</h1>
      <p>Antes de finalizar sua compra, veja se existem cupons Shopee disponíveis para economizar ainda mais.</p>

      <ul>
        <li>🚚 Frete grátis</li>
        <li>🏷️ Cupons de desconto</li>
        <li>🏬 Cupons de loja</li>
        <li>🔥 Ofertas extras por tempo limitado</li>
      </ul>

      <a class="btn" href="{SHOPEE_COUPONS_URL}" target="_blank" rel="nofollow sponsored noopener">Pegar cupons Shopee</a>
      <a class="btn secondary" href="./index.html">Ver ofertas MaryLouse</a>

      <p>MaryLouse Ofertas pode receber comissão por compras feitas pelos links.</p>
    </section>
  </main>
</body>
</html>
"""


def update_sitemap(extra_pages):
    path = Path("sitemap.xml")

    existing = ""

    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")

    urls = set(re.findall(r"<loc>(.*?)</loc>", existing))

    urls.add(f"{SITE_URL}/")

    for page in extra_pages:
        urls.add(f"{SITE_URL}/{page}")

    # Preserva URLs de categoria existentes.
    for file in Path(".").glob("ofertas-*.html"):
        urls.add(f"{SITE_URL}/{file.name}")

    urls.add(f"{SITE_URL}/feed.html")

    today = date.today().isoformat()

    items = []

    for url in sorted(urls):
        priority = "1.0" if url.rstrip("/") == SITE_URL else "0.8"

        items.append(f"""  <url>
    <loc>{esc(url)}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>{priority}</priority>
  </url>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(items)}
</urlset>
"""

    path.write_text(xml, encoding="utf-8", newline="\n")
    print(f"OK: sitemap.xml atualizado com {len(urls)} URLs.")


def main():
    offers = load_offers()

    generated = []

    for page in SPECIAL_PAGES:
        selected = [
            offer for offer in offers
            if marketplace_label(offer.get("marketplace")) == page["marketplace"]
        ]

        selected = selected[:60]

        Path(page["filename"]).write_text(
            layout(page, selected),
            encoding="utf-8",
            newline="\n"
        )

        generated.append(page["filename"])
        print(f"OK: {page['filename']} | {len(selected)} ofertas")

    Path("cupons-shopee.html").write_text(
        cupons_shopee_page(),
        encoding="utf-8",
        newline="\n"
    )

    generated.append("cupons-shopee.html")
    print("OK: cupons-shopee.html")

    update_sitemap(generated)


if __name__ == "__main__":
    main()
