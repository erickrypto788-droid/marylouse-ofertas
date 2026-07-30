from pathlib import Path
from datetime import datetime, timezone, timedelta
import json


OFFERS_PATH = Path("data/offers.json")
AMAZON_MANUAL_MAX_HOURS = 24


def parse_date(value):
    if value is None or value == "":
        return None

    try:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except Exception:
        return None


def is_amazon_manual(offer):
    marketplace = str(offer.get("marketplace") or "").strip().lower()
    source = str(offer.get("source") or "").strip().lower()
    source_type = str(offer.get("source_type") or "").strip().lower()
    manual_id = str(offer.get("manual_id") or "").strip().lower()
    offer_id = str(offer.get("id") or "").strip().lower()

    return (
        marketplace == "amazon"
        or source in {"manual", "manual_csv"}
        or source_type in {"manual", "manual_csv"}
        or manual_id.startswith("manual-amazon")
        or offer_id.startswith("manual-amazon")
    )


def offer_created_at(offer):
    for key in [
        "created_at_iso",
        "created_at",
        "published_at",
        "posted_at",
        "collected_at",
        "updated_at",
    ]:
        dt = parse_date(offer.get(key))

        if dt:
            return dt

    return None


def is_expired(offer, now):
    # Regra geral: se tiver expires_at vencido, remove.
    expires_at = parse_date(offer.get("expires_at"))

    if expires_at and now >= expires_at:
        return True, "expires_at vencido"

    # Segurança extra para Amazon/manual:
    # se não tiver expires_at, considera 24h após criação/publicação.
    if is_amazon_manual(offer):
        created = offer_created_at(offer)

        if created and now >= created + timedelta(hours=AMAZON_MANUAL_MAX_HOURS):
            return True, "Amazon/manual acima de 24h"

    return False, ""


def main():
    if not OFFERS_PATH.exists():
        raise SystemExit("data/offers.json não encontrado.")

    offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))

    if not isinstance(offers, list):
        raise SystemExit("data/offers.json não é uma lista.")

    now = datetime.now(timezone.utc)

    kept = []
    removed = []

    for offer in offers:
        expired, reason = is_expired(offer, now)

        if expired:
            removed.append({
                "id": offer.get("id"),
                "marketplace": offer.get("marketplace"),
                "title": offer.get("title"),
                "reason": reason,
                "expires_at": offer.get("expires_at"),
                "created_at": offer.get("created_at"),
                "published_at": offer.get("published_at"),
            })
        else:
            kept.append(offer)

    OFFERS_PATH.write_text(
        json.dumps(kept, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )

    print(f"[cleanup] Total antes: {len(offers)}")
    print(f"[cleanup] Removidas: {len(removed)}")
    print(f"[cleanup] Total depois: {len(kept)}")

    if removed:
        print()
        print("[cleanup] Exemplos removidos:")

        for item in removed[:30]:
            title = str(item.get("title") or "")[:100]
            print(f"- {item.get('marketplace')} | {item.get('reason')} | {title}")


if __name__ == "__main__":
    main()
