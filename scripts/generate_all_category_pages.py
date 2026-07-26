from pathlib import Path
from datetime import datetime, timezone
import json
import re
import html
import unicodedata
from urllib.parse import quote


SITE_URL = "https://marylouse-ofertas.vercel.app"

ROOT = Path(".")
OFFERS_PATH = ROOT / "data" / "offers.json"
LOGO_PATH = "assets/logo.png"

CATEGORY_DEFS = [
    {
        "label": "Supermercados",
        "category": "Supermercados",
        "slug": "supermercados",
        "emoji": "🛒",
        "seo_title": "Ofertas de Supermercado Hoje",
        "seo_description": "Veja ofertas atualizadas de supermercado, produtos de limpeza, higiene, fraldas, alimentos e itens recorrentes para economizar todos os dias.",
    },
    {
        "label": "Celulares",
        "category": "Celulares",
        "slug": "celulares",
        "emoji": "📱",
        "seo_title": "Ofertas de Celulares Hoje",
        "seo_description": "Confira promoções de celulares, smartphones Xiaomi, Samsung, Motorola, iPhone e acessórios selecionados em lojas parceiras.",
    },
    {
        "label": "Eletrônicos",
        "category": "Eletrônicos",
        "slug": "eletronicos",
        "emoji": "🎧",
        "seo_title": "Ofertas de Eletrônicos Hoje",
        "seo_description": "Veja ofertas de eletrônicos, fones, caixas de som, gadgets, acessórios e produtos úteis com descontos atualizados.",
    },
    {
        "label": "Informática",
        "category": "Informática",
        "slug": "informatica",
        "emoji": "💻",
        "seo_title": "Ofertas de Informática Hoje",
        "seo_description": "Ofertas de notebooks, monitores, SSDs, processadores, periféricos, impressoras e acessórios de informática.",
    },
    {
        "label": "Games",
        "category": "Games",
        "slug": "games",
        "emoji": "🎮",
        "seo_title": "Ofertas de Games Hoje",
        "seo_description": "Promoções de games, consoles, controles, acessórios gamer e produtos para quem gosta de jogar economizando.",
    },
    {
        "label": "Casa e Cozinha",
        "category": "Casa e Cozinha",
        "slug": "casa-cozinha",
        "emoji": "🍳",
        "seo_title": "Ofertas de Casa e Cozinha Hoje",
        "seo_description": "Achadinhos e ofertas de casa e cozinha: air fryer, panelas, utensílios, organizadores, móveis e itens úteis para o dia a dia.",
    },
    {
        "label": "Eletrodomésticos",
        "category": "Eletrodomésticos",
        "slug": "eletrodomesticos",
        "emoji": "🔌",
        "seo_title": "Ofertas de Eletrodomésticos Hoje",
        "seo_description": "Ofertas de eletrodomésticos e utilidades para casa, com produtos selecionados em marketplaces parceiros.",
    },
    {
        "label": "Moda Feminina",
        "category": "Moda Feminina",
        "slug": "moda-feminina",
        "emoji": "👗",
        "seo_title": "Ofertas de Moda Feminina Hoje",
        "seo_description": "Promoções de moda feminina, roupas, conjuntos, leggings, vestidos, blusas e achadinhos para economizar.",
    },
    {
        "label": "Moda Masculina",
        "category": "Moda Masculina",
        "slug": "moda-masculina",
        "emoji": "👕",
        "seo_title": "Ofertas de Moda Masculina Hoje",
        "seo_description": "Ofertas de moda masculina, camisetas, camisas, bermudas, calças e peças úteis com descontos atualizados.",
    },
    {
        "label": "Moda Plus Size",
        "category": "Moda Plus Size",
        "slug": "moda-plus-size",
        "emoji": "✨",
        "seo_title": "Ofertas de Moda Plus Size Hoje",
        "seo_description": "Promoções de moda plus size, roupas confortáveis e achadinhos selecionados para economizar.",
    },
    {
        "label": "Moda Infantil",
        "category": "Moda Infantil",
        "slug": "moda-infantil",
        "emoji": "🧒",
        "seo_title": "Ofertas de Moda Infantil Hoje",
        "seo_description": "Ofertas de moda infantil, roupas para crianças, calçados infantis e produtos úteis para o dia a dia.",
    },
    {
        "label": "Calçados",
        "category": "Calçados",
        "slug": "calcados",
        "emoji": "👟",
        "seo_title": "Ofertas de Calçados Hoje",
        "seo_description": "Promoções de tênis, sandálias, botas, chinelos, sapatênis e calçados femininos, masculinos e infantis.",
    },
    {
        "label": "Bolsas",
        "category": "Bolsas",
        "slug": "bolsas",
        "emoji": "👜",
        "seo_title": "Ofertas de Bolsas e Mochilas Hoje",
        "seo_description": "Ofertas de bolsas, mochilas, malas, necessaires, carteiras e acessórios úteis para trabalho, estudo e viagem.",
    },
    {
        "label": "Beleza",
        "category": "Beleza",
        "slug": "beleza",
        "emoji": "💄",
        "seo_title": "Ofertas de Beleza Hoje",
        "seo_description": "Promoções de beleza, perfumes, cabelo, maquiagem, skincare, barbeadores, secadores e chapinhas.",
    },
    {
        "label": "Esportes",
        "category": "Esportes",
        "slug": "esportes",
        "emoji": "🏋️",
        "seo_title": "Ofertas de Esportes e Fitness Hoje",
        "seo_description": "Ofertas de produtos esportivos, academia, fitness, bicicletas, bolas, halteres, roupas de treino e acessórios.",
    },
    {
        "label": "Brinquedos",
        "category": "Brinquedos e Hobbies",
        "slug": "brinquedos",
        "emoji": "🧸",
        "seo_title": "Ofertas de Brinquedos Hoje",
        "seo_description": "Promoções de brinquedos, jogos, hobbies, produtos infantis, Hot Wheels, bonecos e itens divertidos.",
    },
    {
        "label": "Mãe e Bebê",
        "category": "Mãe e Bebê",
        "slug": "mae-bebe",
        "emoji": "🍼",
        "seo_title": "Ofertas para Mãe e Bebê Hoje",
        "seo_description": "Ofertas de fraldas, lenços umedecidos, mamadeiras, produtos para bebê e itens úteis para maternidade.",
    },
    {
        "label": "Pet",
        "category": "Pet",
        "slug": "pet",
        "emoji": "🐶",
        "seo_title": "Ofertas Pet Hoje",
        "seo_description": "Promoções de produtos para cães e gatos, rações, areia higiênica, brinquedos, comedouros e acessórios pet.",
    },
    {
        "label": "Saúde",
        "category": "Saúde",
        "slug": "saude",
        "emoji": "❤️",
        "seo_title": "Ofertas de Saúde Hoje",
        "seo_description": "Ofertas de produtos de saúde, monitores de pressão, termômetros, inaladores, balanças, oxímetros e itens úteis.",
    },
    {
        "label": "Papelaria",
        "category": "Papelaria",
        "slug": "papelaria",
        "emoji": "📚",
        "seo_title": "Ofertas de Papelaria Hoje",
        "seo_description": "Promoções de papelaria, canetas, cadernos, materiais escolares, estojos, agendas e itens para estudo.",
    },
    {
        "label": "Ferramentas",
        "category": "Ferramentas",
        "slug": "ferramentas",
        "emoji": "🧰",
        "seo_title": "Ofertas de Ferramentas Hoje",
        "seo_description": "Ofertas de ferramentas, furadeiras, parafusadeiras, kits, trenas, alicates e itens úteis para casa e trabalho.",
    },
    {
        "label": "Outros",
        "category": "Outros",
        "slug": "outros",
        "emoji": "📦",
        "seo_title": "Outras Ofertas Hoje",
        "seo_description": "Outras ofertas e achadinhos selecionados pela MaryLouse Ofertas em marketplaces parceiros.",
    },
]


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
    "Sneakers": "Calçados",
    "Sandals And Clogs": "Calçados",
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

    # Prioridades importantes
    if has(text, [
        "monitor de pressao", "pressao arterial", "aparelho de pressao",
        "termometro", "inalador", "nebulizador", "oximetro", "glicose",
        "bioimpedancia", "balanca digital", "massageador"
    ]):
        return "Saúde"

    if has(text, [
        "notebook", "laptop", "macbook", "chromebook", "pc gamer", "asus tuf",
        "tuf gaming", "rtx", "gtx", "geforce", "ryzen", "intel core",
        "processador", "placa de video", "placa mae", "ssd", "hd externo",
        "memoria ram", "teclado", "mouse", "webcam", "roteador", "impressora",
        "toner", "cartucho", "hub usb", "pendrive", "fonte notebook"
    ]):
        return "Informática"

    if has(text, [
        "smartphone", "celular", "iphone", "galaxy", "xiaomi", "redmi", "poco",
        "motorola", "samsung s", "android", "5g", "capinha", "capa celular",
        "pelicula", "carregador celular", "power bank"
    ]):
        return "Celulares"

    if has(text, [
        "fralda", "pampers", "huggies", "mamypoko", "mamy poko", "mamy poko",
        "lenco umedecido", "mamadeira", "chupeta", "bebe", "baby",
        "cadeirinha", "carrinho de bebe", "berco"
    ]):
        return "Mãe e Bebê"

    if has(text, [
        "mochila", "bolsa", "mala", "necessaire", "pochete", "carteira feminina",
        "carteira masculina", "backpack", "maleta", "kit organizador de malas",
        "saco a vacuo", "saco organizador"
    ]):
        return "Bolsas"

    if has(text, [
        "tenis", "sapatennis", "sapato", "sandalia", "chinelo", "bota",
        "sneaker", "slip on", "calcado", "rasteirinha", "scarpin", "coturno"
    ]):
        return "Calçados"

    if has(text, [
        "painel para tv", "painel tv", "rack para tv", "rack para sala",
        "sala de estar", "cadeira escritorio", "cadeira presidente",
        "cadeira gamer", "mesa computador", "mesa para computador",
        "escrivaninha", "mesa gamer", "fruteira", "cesto multiuso",
        "organizador de cozinha", "tapete", "luminaria", "lampada"
    ]):
        return "Casa e Cozinha"

    if has(text, [
        "barbeador", "aparador", "perfume", "body splash", "hidratante",
        "shampoo", "condicionador", "protetor solar", "maquiagem", "batom",
        "secador", "chapinha", "escova secadora", "alisadora", "creme",
        "skin care"
    ]):
        return "Beleza"

    if has(text, [
        "air fryer", "panela", "frigideira", "cafeteira", "liquidificador",
        "batedeira", "mixer", "microondas", "micro ondas", "garrafa", "copo",
        "xicara", "jogo de cama", "toalha", "cozinha", "utensilio"
    ]):
        return "Casa e Cozinha"

    if has(text, [
        "geladeira", "fogao", "cooktop", "lavadora", "maquina de lavar",
        "ar condicionado", "ventilador", "purificador de ar", "aspirador de po"
    ]):
        return "Eletrodomésticos"

    if has(text, [
        "racao", "cachorro", "gato", "areia higienica", "coleira",
        "arranhador", "bebedouro pet", "comedouro", "brinquedo pet"
    ]) or " pet " in f" {text} ":
        return "Pet"

    if has(text, [
        "papel higienico", "detergente", "amaciante", "sabao em po",
        "sabonete", "creme dental", "desinfetante", "saco de lixo",
        "papel toalha", "arroz", "feijao", "azeite", "oleo de soja",
        "supermercado", "lava roupas"
    ]):
        return "Supermercados"

    if has(text, [
        "playstation", "ps5", "ps4", "xbox", "nintendo", "switch", "console",
        "controle gamer", "joystick", "gamepad", "videogame", "video game"
    ]):
        return "Games"

    if has(text, [
        "hot wheels", "lego", "boneca", "boneco", "brinquedo", "jogo da forca",
        "quebra cabeca", "carrinho brinquedo"
    ]):
        return "Brinquedos e Hobbies"

    if has(text, [
        "halter", "halteres", "academia", "fitness", "bike spinning",
        "bicicleta", "bola futebol", "bola de futebol", "yoga", "whey",
        "creatina", "esteira", "luva academia", "corrida"
    ]):
        return "Esportes"

    if has(text, [
        "caneta", "lapis", "caderno", "agenda", "marca texto", "marcador",
        "papel sulfite", "estojo escolar", "maleta pintura", "kit pintura",
        "material escolar", "papelaria"
    ]):
        return "Papelaria"

    if has(text, [
        "furadeira", "parafusadeira", "chave de fenda", "martelo", "serra",
        "trena", "alicate", "kit ferramentas", "ferramenta"
    ]):
        return "Ferramentas"

    if has(text, ["plus size", "moda plus size", "roupas plus size"]):
        return "Moda Plus Size"

    if has(text, [
        "vestido", "blusa feminina", "cropped", "saia", "legging",
        "calca legging", "top feminino", "conjunto feminino", "feminina esportiva"
    ]):
        return "Moda Feminina"

    if has(text, [
        "camiseta masculina", "camisa masculina", "calca masculina",
        "bermuda masculina", "cueca", "masculino"
    ]):
        return "Moda Masculina"

    if has(text, [
        "infantil", "menino", "menina", "crianca", "kids", "roupa infantil"
    ]):
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
    )


def get_old_price(offer):
    return (
        offer.get("old_price_text")
        or offer.get("original_price_text")
        or format_brl(offer.get("old_price"))
        or format_brl(offer.get("original_price"))
        or ""
    )


def discount_label(offer):
    value = offer.get("discount_percent")

    try:
        number = float(value or 0)
    except Exception:
        number = 0

    if number > 0:
        return f"{number:.0f}% OFF"

    return "Oferta"


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


def offer_url(offer):
    return (
        offer.get("affiliate_url")
        or offer.get("url")
        or offer.get("link")
        or offer.get("product_url")
        or "#"
    )


def offer_image(offer):
    return (
        offer.get("image_url")
        or offer.get("image")
        or offer.get("thumbnail")
        or "assets/logo.png"
    )


def escape(value):
    return html.escape(str(value or ""), quote=True)


def short(value, limit=150):
    text = str(value or "").strip()

    if len(text) <= limit:
        return text

    return text[:limit - 1].rstrip() + "…"


def load_offers():
    if not OFFERS_PATH.exists():
        raise SystemExit("data/offers.json não encontrado.")

    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        raise SystemExit("data/offers.json não é uma lista.")

    for offer in offers:
        offer["_category"] = canonical_category(offer)
        offer["_created_ts"] = parse_ts(offer)

    offers.sort(key=lambda o: o.get("_created_ts") or 0, reverse=True)

    return offers


def category_nav(counts):
    links = []

    for cat in CATEGORY_DEFS:
        label = cat["label"]
        count = counts.get(cat["category"], 0)
        url = f"ofertas-{cat['slug']}.html"
        links.append(
            f'<a class="pill" href="{url}"><span>{cat["emoji"]}</span> {escape(label)} <small>({count})</small></a>'
        )

    return "\n".join(links)


def card_html(offer):
    title = offer.get("title") or "Oferta"
    category = offer.get("_category") or "Outros"
    marketplace = marketplace_label(offer.get("marketplace"))
    url = offer_url(offer)
    image = offer_image(offer)
    price = get_price(offer)
    old = get_old_price(offer)
    discount = discount_label(offer)

    desc = offer.get("description") or offer.get("caption") or "Oferta selecionada pela MaryLouse Ofertas."

    old_html = ""

    if old:
        old_html = f'<div class="old">De: <span>{escape(old)}</span></div>'
    else:
        old_html = '<div class="old">Oferta por tempo limitado</div>'

    price_html = escape(price or "Ver preço")

    return f"""
    <article class="card">
      <a href="{escape(url)}" target="_blank" rel="nofollow sponsored noopener" class="image-wrap">
        <img src="{escape(image)}" alt="{escape(title)}" loading="lazy" />
        <span class="badge">{escape(discount)}</span>
        <span class="store">{escape(marketplace)}</span>
      </a>
      <div class="card-body">
        <div class="cat">{escape(category)}</div>
        <h2>{escape(short(title, 88))}</h2>
        <p>{escape(short(desc, 130))}</p>
        <div class="price-box">
          {old_html}
          <div class="price-line">
            <span>Por apenas</span>
            <strong>{price_html}</strong>
          </div>
        </div>
        <a class="buy" href="{escape(url)}" target="_blank" rel="nofollow sponsored noopener">🛒 Comprar agora</a>
      </div>
    </article>
    """


def page_html(cat, offers, counts):
    label = cat["label"]
    category = cat["category"]
    slug = cat["slug"]
    emoji = cat["emoji"]

    page_url = f"{SITE_URL}/ofertas-{slug}.html"
    page_title = f"{cat['seo_title']} | MaryLouse Ofertas"
    description = cat["seo_description"]

    cards = "\n".join(card_html(o) for o in offers)

    if not cards:
        cards = f"""
        <div class="empty">
          <h2>Nenhuma oferta disponível agora em {escape(label)}.</h2>
          <p>As ofertas mudam ao longo do dia. Volte em breve ou veja todas as categorias.</p>
          <a href="./index.html#categorias">Ver todas as categorias</a>
        </div>
        """

    updated = datetime.now().strftime("%d/%m/%Y %H:%M")
    nav = category_nav(counts)

    json_ld_items = []

    for index, offer in enumerate(offers[:20], start=1):
        json_ld_items.append({
            "@type": "ListItem",
            "position": index,
            "url": offer_url(offer),
            "name": offer.get("title") or "Oferta"
        })

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": page_title,
        "itemListElement": json_ld_items
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>{escape(page_title)}</title>
  <meta name="description" content="{escape(description)}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <link rel="canonical" href="{escape(page_url)}" />
  <link rel="icon" type="image/svg+xml" href="./assets/favicon.svg" />
  <meta name="theme-color" content="#ff2f7d" />

  <meta property="og:type" content="website" />
  <meta property="og:title" content="{escape(page_title)}" />
  <meta property="og:description" content="{escape(description)}" />
  <meta property="og:url" content="{escape(page_url)}" />
  <meta property="og:image" content="{SITE_URL}/assets/logo.png" />

  <script type="application/ld+json">
  {json_ld}
  </script>

  <style>
    :root {{
      --pink: #ef2473;
      --pink-dark: #cc155a;
      --green: #08a64b;
      --ink: #1f1720;
      --muted: #6e5e67;
      --border: #f0d7df;
      --bg: #fff4f7;
      --soft: #fffafd;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: Inter, Arial, Helvetica, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #ffe0cf, transparent 34%),
        linear-gradient(180deg, #fff5f8, #fff);
    }}

    a {{ color: inherit; }}

    .header {{
      position: sticky;
      top: 0;
      z-index: 20;
      background: rgba(255,255,255,.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }}

    .header-inner {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 14px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      font-weight: 950;
      font-size: 24px;
      color: #064750;
    }}

    .brand img {{
      width: 54px;
      height: 54px;
      border-radius: 16px;
      object-fit: cover;
    }}

    .nav {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}

    .nav a {{
      text-decoration: none;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 10px 15px;
      font-weight: 900;
      color: var(--muted);
      background: #fff;
      box-shadow: 0 8px 18px rgba(120, 30, 70, .08);
    }}

    .nav .telegram {{
      background: #1c9bd7;
      color: #fff;
      border-color: #1c9bd7;
    }}

    .hero {{
      max-width: 1180px;
      margin: 34px auto 20px;
      padding: 0 20px;
    }}

    .hero-card {{
      background: rgba(255,255,255,.86);
      border: 1px solid var(--border);
      border-radius: 34px;
      padding: 34px;
      box-shadow: 0 18px 45px rgba(154, 41, 92, .10);
    }}

    .kicker {{
      display: inline-flex;
      gap: 8px;
      align-items: center;
      padding: 10px 16px;
      border-radius: 999px;
      background: #fff0f6;
      color: var(--pink-dark);
      font-weight: 950;
      border: 1px solid #ffc7dc;
      margin-bottom: 18px;
    }}

    h1 {{
      font-size: clamp(34px, 6vw, 62px);
      line-height: 1.02;
      margin: 0 0 14px;
      letter-spacing: -2px;
    }}

    .hero p {{
      color: var(--muted);
      font-size: 19px;
      line-height: 1.55;
      max-width: 820px;
      margin: 0;
    }}

    .actions {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 24px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      padding: 14px 20px;
      font-weight: 950;
      text-decoration: none;
      border: 1px solid var(--border);
      background: #fff;
    }}

    .btn.primary {{
      background: var(--pink);
      color: #fff;
      border-color: var(--pink);
      box-shadow: 0 12px 26px rgba(239, 36, 115, .22);
    }}

    .section {{
      max-width: 1180px;
      margin: 24px auto;
      padding: 0 20px;
    }}

    .category-box {{
      background: rgba(255,255,255,.88);
      border: 1px solid var(--border);
      border-radius: 28px;
      padding: 24px;
      box-shadow: 0 12px 30px rgba(154, 41, 92, .08);
    }}

    .category-box h2 {{
      margin: 0 0 8px;
      font-size: 28px;
    }}

    .pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}

    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--border);
      text-decoration: none;
      background: #fff;
      font-weight: 900;
      color: var(--muted);
    }}

    .pill.active {{
      background: var(--pink);
      color: #fff;
      border-color: var(--pink);
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 22px;
      margin-top: 22px;
    }}

    .card {{
      overflow: hidden;
      border-radius: 26px;
      background: #fff;
      border: 1px solid var(--border);
      box-shadow: 0 14px 30px rgba(126, 34, 80, .10);
    }}

    .image-wrap {{
      position: relative;
      display: block;
      height: 255px;
      background: #fff;
      overflow: hidden;
    }}

    .image-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }}

    .badge {{
      position: absolute;
      left: 14px;
      top: 14px;
      background: #ffb000;
      color: #221;
      padding: 9px 12px;
      border-radius: 999px;
      font-weight: 950;
      box-shadow: 0 8px 18px rgba(0,0,0,.12);
    }}

    .store {{
      position: absolute;
      right: 14px;
      top: 14px;
      background: #fff;
      color: var(--pink-dark);
      padding: 9px 12px;
      border-radius: 999px;
      font-weight: 950;
      box-shadow: 0 8px 18px rgba(0,0,0,.12);
    }}

    .card-body {{
      padding: 18px;
    }}

    .cat {{
      color: var(--pink-dark);
      font-size: 13px;
      font-weight: 950;
      text-transform: uppercase;
      margin-bottom: 8px;
    }}

    .card h2 {{
      margin: 0 0 10px;
      font-size: 20px;
      line-height: 1.22;
    }}

    .card p {{
      color: var(--muted);
      line-height: 1.45;
      min-height: 58px;
      margin: 0 0 14px;
    }}

    .price-box {{
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
      font-size: 26px;
      font-weight: 950;
      white-space: nowrap;
    }}

    .buy {{
      display: flex;
      justify-content: center;
      align-items: center;
      text-decoration: none;
      background: linear-gradient(135deg, #10b960, #07863b);
      color: #fff;
      border-radius: 16px;
      padding: 14px 16px;
      font-weight: 950;
      box-shadow: 0 12px 22px rgba(0, 128, 59, .18);
    }}

    .empty {{
      grid-column: 1 / -1;
      padding: 28px;
      border-radius: 24px;
      border: 1px solid var(--border);
      background: #fff;
      text-align: center;
    }}

    .footer {{
      max-width: 1180px;
      margin: 44px auto 24px;
      padding: 0 20px;
      color: var(--muted);
      text-align: center;
      font-size: 14px;
    }}

    @media (max-width: 960px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}

    @media (max-width: 640px) {{
      .header-inner {{
        align-items: flex-start;
        flex-direction: column;
      }}

      .grid {{ grid-template-columns: 1fr; }}

      .hero-card {{
        padding: 24px;
        border-radius: 24px;
      }}

      .image-wrap {{
        height: 230px;
      }}
    }}
  </style>
</head>

<body>
  <header class="header">
    <div class="header-inner">
      <a class="brand" href="./index.html">
        <img src="./{LOGO_PATH}" alt="MaryLouse Ofertas" />
        <span>MaryLouse Ofertas</span>
      </a>

      <nav class="nav">
        <a href="./index.html#ofertas">🔥 Ofertas</a>
        <a href="./index.html#categorias">🧭 Categorias</a>
        <a class="telegram" href="https://t.me/dmaispromo" target="_blank" rel="noopener">📲 Telegram</a>
        <a href="https://s.shopee.com.br/111NhMP4uM" target="_blank" rel="nofollow sponsored noopener">🎟️ Cupons Shopee</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="hero">
      <div class="hero-card">
        <div class="kicker">{emoji} Categoria atualizada automaticamente</div>
        <h1>{escape(cat["seo_title"])}</h1>
        <p>{escape(description)}</p>

        <div class="actions">
          <a class="btn primary" href="#ofertas">Ver ofertas de {escape(label)}</a>
          <a class="btn" href="./index.html">Ver todas as ofertas</a>
        </div>
      </div>
    </section>

    <section class="section" id="categorias">
      <div class="category-box">
        <h2>🧭 Explore outras categorias</h2>
        <p>Escolha uma categoria para ver ofertas atualizadas.</p>
        <div class="pills">
          <a class="pill" href="./index.html#ofertas">✨ Todos</a>
          {nav}
        </div>
      </div>
    </section>

    <section class="section" id="ofertas">
      <div class="category-box">
        <h2>{emoji} {escape(label)} <small>({len(offers)} ofertas)</small></h2>
        <p>Ofertas atualizadas em {escape(updated)}. Os preços e disponibilidade podem mudar a qualquer momento.</p>

        <div class="grid">
          {cards}
        </div>
      </div>
    </section>
  </main>

  <footer class="footer">
    <p>MaryLouse Ofertas pode receber comissão por compras feitas pelos links. Verifique preço e disponibilidade na loja antes de concluir a compra.</p>
  </footer>
</body>
</html>
"""


def write_sitemap(category_pages):
    urls = [
        f"{SITE_URL}/",
    ]

    for page in category_pages:
        urls.append(f"{SITE_URL}/{page}")

    today = datetime.now().date().isoformat()

    items = []

    for url in urls:
        items.append(f"""  <url>
    <loc>{escape(url)}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>{'1.0' if url.endswith('/') else '0.8'}</priority>
  </url>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(items)}
</urlset>
"""

    Path("sitemap.xml").write_text(xml, encoding="utf-8", newline="\n")


def main():
    offers = load_offers()

    counts = {}

    for offer in offers:
        cat = offer.get("_category") or "Outros"
        counts[cat] = counts.get(cat, 0) + 1

    generated = []

    for cat in CATEGORY_DEFS:
        category = cat["category"]
        category_offers = [o for o in offers if o.get("_category") == category]
        filename = f"ofertas-{cat['slug']}.html"

        Path(filename).write_text(
            page_html(cat, category_offers, counts),
            encoding="utf-8",
            newline="\n"
        )

        generated.append(filename)
        print(f"OK: {filename} | {len(category_offers)} ofertas")

    write_sitemap(generated)

    print()
    print(f"Total de páginas geradas: {len(generated)}")
    print("OK: sitemap.xml atualizado.")


if __name__ == "__main__":
    main()
