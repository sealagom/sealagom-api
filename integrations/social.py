"""Post new warnings to X, Facebook, Instagram, Threads, Telegram, Discord, Slack, Mastodon or
Bluesky: one poll loop, one short post per warning, one publisher per platform.

    pip install requests requests-oauthlib pillow
    export SEALAGOM_API_KEY=...                      # https://www.sealagom.com/profile/?tab=api
    python social.py --navarea 1 --severity critical --to telegram,x       # every 15 minutes from cron
    python social.py --feed military --to discord --once                   # one pass

Filters: --navarea ID (repeatable), --coastal ID, --country, --feed <slug> (Full API), --severity
critical|high. The script remembers what it posted in sealagom-social-state.json next to it.

Keys, by platform (environment variables):
  X (Twitter)   X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET  (a free developer app; OAuth 1.0a user context)
  Facebook Page FB_PAGE_ID, FB_PAGE_TOKEN                                 (Graph API page token with pages_manage_posts)
  Instagram     IG_USER_ID, IG_ACCESS_TOKEN                               (Instagram Graph API; a business account; posts need an image, made here)
  Threads       THREADS_USER_ID, THREADS_ACCESS_TOKEN                      (Threads API)
  Telegram      TG_BOT_TOKEN, TG_CHAT_ID                                   (channel or group; the bot is an admin)
  Discord       DISCORD_WEBHOOK_URL
  Slack         SLACK_WEBHOOK_URL
  Mastodon      MASTODON_BASE_URL, MASTODON_TOKEN
  Bluesky       BSKY_HANDLE, BSKY_APP_PASSWORD

Each post: "<region> <number>: <headline> [<severity>]" and the link; the warning text is the
authority. Credit SeaLagom, www.sealagom.com, on the account. Grok reads X, so a posting account
is also what Grok sees; for Grok as a model use openai_compatible.py with https://api.x.ai/v1.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import pathlib
import sys
import time

import requests

SEALAGOM = "https://www.sealagom.com"
HEADERS = {"X-API-Token": os.environ.get("SEALAGOM_API_KEY", ""), "Accept": "application/json", "User-Agent": "sealagom-social/1.0"}
STATE = pathlib.Path(__file__).with_name("sealagom-social-state.json")


# -- the warnings ------------------------------------------------------------------------------

def fetch(args) -> list[dict]:
    params: list[tuple[str, str]] = [("ai_in_force", "true"), ("include_ai_analysis", "true"), ("page_size", "50")]
    for n in args.navarea or []:
        params.append(("navarea_id", str(n)))
    for c in args.coastal or []:
        params.append(("coastal_id", str(c)))
    if args.country:
        params.append(("country", args.country))
    if args.severity:
        params.append(("ai_severity", args.severity))
    path = f"/api/v2/feeds/{args.feed}/" if args.feed else "/api/v2/messages/"
    r = requests.get(f"{SEALAGOM}{path}", params=params, headers=HEADERS, timeout=60)
    d = r.json()
    if r.status_code >= 400:
        up = d.get("upgrade") or (d.get("meta") or {}).get("upgrade")
        sys.exit(f"{d.get('detail')}" + (f" Plan {up['plan']}, {up['monthly_usd']} USD a month: {up['plans']}" if up else ""))
    return d.get("results") or []


def key_of(w: dict) -> str:
    return f"{w.get('scope')}:{w.get('region_id')}:{w.get('number')}"


def text_of(w: dict, limit: int = 280) -> str:
    ai = w.get("ai_analysis") or {}
    head = f"{w.get('region_title') or ''} {w.get('number') or ''}".strip()
    line = head + (f": {ai['headline']}" if ai.get("headline") else "") + (f" [{ai['severity']}]" if ai.get("severity") else "")
    url = f"{SEALAGOM}/{w.get('scope')}/{w.get('region_id')}/message/{w.get('id')}/"
    room = limit - len(url) - 1 - 20  # the link and " via SeaLagom"
    if len(line) > room:
        line = line[: room - 1] + "…"
    return f"{line}\n{url} via SeaLagom"


def image_of(w: dict) -> bytes:
    """A plain card (1080x1080 PNG) for the platforms that need a picture: dark green, the headline, the number."""
    from PIL import Image, ImageDraw, ImageFont

    ai = w.get("ai_analysis") or {}
    img = Image.new("RGB", (1080, 1080), (2, 15, 11))
    d = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("arial.ttf", 64)
        small = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        big = small = ImageFont.load_default()
    d.text((80, 120), f"{w.get('region_title') or ''} {w.get('number') or ''}", fill=(50, 127, 85), font=small)
    words, lines, cur = (ai.get("headline") or (w.get("content_en") or w.get("content") or "")[:120]).split(), [], ""
    for word in words:
        if len(cur) + len(word) + 1 > 26:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    lines.append(cur)
    y = 240
    for ln in lines[:8]:
        d.text((80, y), ln, fill=(244, 248, 245), font=big)
        y += 84
    d.text((80, 960), "www.sealagom.com", fill=(120, 153, 132), font=small)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# -- the publishers ----------------------------------------------------------------------------

def post_x(text: str, _w: dict) -> None:
    from requests_oauthlib import OAuth1

    auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    r = requests.post("https://api.x.com/2/tweets", json={"text": text}, auth=auth, timeout=30)
    r.raise_for_status()


def post_facebook(text: str, w: dict) -> None:
    page = os.environ["FB_PAGE_ID"]
    url = f"{SEALAGOM}/{w.get('scope')}/{w.get('region_id')}/message/{w.get('id')}/"
    r = requests.post(f"https://graph.facebook.com/v21.0/{page}/feed", data={"message": text, "link": url, "access_token": os.environ["FB_PAGE_TOKEN"]}, timeout=30)
    r.raise_for_status()


def post_instagram(text: str, w: dict) -> None:
    """Instagram needs a public image URL: the card is uploaded to the free image host of your choice;
    here it goes through 0x0.st (replace with your own bucket for anything serious)."""
    user, token = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    up = requests.post("https://0x0.st", files={"file": ("card.png", image_of(w), "image/png")}, timeout=60)
    up.raise_for_status()
    c = requests.post(f"https://graph.facebook.com/v21.0/{user}/media", data={"image_url": up.text.strip(), "caption": text, "access_token": token}, timeout=60).json()
    r = requests.post(f"https://graph.facebook.com/v21.0/{user}/media_publish", data={"creation_id": c["id"], "access_token": token}, timeout=60)
    r.raise_for_status()


def post_threads(text: str, _w: dict) -> None:
    user, token = os.environ["THREADS_USER_ID"], os.environ["THREADS_ACCESS_TOKEN"]
    c = requests.post(f"https://graph.threads.net/v1.0/{user}/threads", data={"media_type": "TEXT", "text": text[:500], "access_token": token}, timeout=60).json()
    r = requests.post(f"https://graph.threads.net/v1.0/{user}/threads_publish", data={"creation_id": c["id"], "access_token": token}, timeout=60)
    r.raise_for_status()


def post_telegram(text: str, _w: dict) -> None:
    r = requests.post(f"https://api.telegram.org/bot{os.environ['TG_BOT_TOKEN']}/sendMessage",
                      json={"chat_id": os.environ["TG_CHAT_ID"], "text": text, "disable_web_page_preview": False}, timeout=30)
    r.raise_for_status()


def post_discord(text: str, _w: dict) -> None:
    requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={"content": text}, timeout=30).raise_for_status()


def post_slack(text: str, _w: dict) -> None:
    requests.post(os.environ["SLACK_WEBHOOK_URL"], json={"text": text}, timeout=30).raise_for_status()


def post_mastodon(text: str, _w: dict) -> None:
    r = requests.post(f"{os.environ['MASTODON_BASE_URL'].rstrip('/')}/api/v1/statuses", data={"status": text[:500]},
                      headers={"Authorization": f"Bearer {os.environ['MASTODON_TOKEN']}"}, timeout=30)
    r.raise_for_status()


def post_bluesky(text: str, _w: dict) -> None:
    s = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession",
                      json={"identifier": os.environ["BSKY_HANDLE"], "password": os.environ["BSKY_APP_PASSWORD"]}, timeout=30).json()
    record = {"$type": "app.bsky.feed.post", "text": text[:300], "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    r = requests.post("https://bsky.social/xrpc/com.atproto.repo.createRecord", json={"repo": s["did"], "collection": "app.bsky.feed.post", "record": record},
                      headers={"Authorization": f"Bearer {s['accessJwt']}"}, timeout=30)
    r.raise_for_status()


PUBLISHERS = {"x": (post_x, 280), "facebook": (post_facebook, 2000), "instagram": (post_instagram, 2000), "threads": (post_threads, 500),
              "telegram": (post_telegram, 4000), "discord": (post_discord, 2000), "slack": (post_slack, 4000), "mastodon": (post_mastodon, 500),
              "bluesky": (post_bluesky, 300)}


# -- the loop ------------------------------------------------------------------------------------

def run(args) -> None:
    seen: dict = json.loads(STATE.read_text()) if STATE.exists() else {}
    targets = [t.strip() for t in args.to.split(",") if t.strip()]
    unknown = [t for t in targets if t not in PUBLISHERS]
    if unknown:
        sys.exit(f"unknown platform(s) {unknown}; choose from {', '.join(PUBLISHERS)}")
    while True:
        new = [w for w in fetch(args) if key_of(w) not in seen]
        if not seen and not args.backfill:
            # First run: remember what is in force now, post only what arrives later.
            for w in new:
                seen[key_of(w)] = w.get("added_on")
            new = []
        for w in sorted(new, key=lambda x: x.get("added_on") or ""):
            for t in targets:
                fn, limit = PUBLISHERS[t]
                try:
                    fn(text_of(w, limit), w)
                    print(f"posted {key_of(w)} to {t}")
                except Exception as exc:  # noqa: BLE001
                    print(f"failed {key_of(w)} to {t}: {str(exc)[:200]}", file=sys.stderr)
            seen[key_of(w)] = w.get("added_on")
        STATE.write_text(json.dumps(seen))
        if args.once:
            return
        time.sleep(args.every * 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Post new SeaLagom warnings to social platforms.")
    ap.add_argument("--to", required=True, help="comma-separated: " + ", ".join(PUBLISHERS))
    ap.add_argument("--navarea", type=int, action="append")
    ap.add_argument("--coastal", type=int, action="append")
    ap.add_argument("--country")
    ap.add_argument("--feed", help="a themed feed slug (Full API)")
    ap.add_argument("--severity", choices=["critical", "high", "medium", "low"])
    ap.add_argument("--every", type=int, default=15, help="minutes between polls")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--backfill", action="store_true", help="post what is in force now on the first run too")
    run(ap.parse_args())
