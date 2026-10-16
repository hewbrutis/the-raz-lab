"""MandMs3DPrints local shop — KIKI-owned storefront + demo API + bench editor."""
from __future__ import print_function

import json
import os
import re
import sys
import threading
import uuid
from datetime import datetime

try:
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlencode, urlparse
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except ImportError:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from SocketServer import ThreadingTCPServer as ThreadingHTTPServer
    from urlparse import parse_qs, urlparse
    from urllib import urlencode
    from urllib2 import Request, urlopen, URLError, HTTPError

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8791"))
if "HOST" in os.environ:
    HOST = os.environ.get("HOST") or "127.0.0.1"
elif "PORT" in os.environ:
    # Cloud hosts (Render and the like) set PORT and need all interfaces.
    HOST = "0.0.0.0"
else:
    HOST = "127.0.0.1"
ORDERS = []
STRIPE_CHECKOUT_URL = "https://api.stripe.com/v1/checkout/sessions"
CATALOG_LOCK = threading.Lock()
LOCAL_HOSTS = set(["127.0.0.1", "::1", "localhost"])
VIDEO_LOCK = threading.Lock()
VIDEO_DIR = os.environ.get(
    "MANDMS_VIDEO_DIR",
    r"C:\Users\Matt\Desktop\StarNet Trusted\STARNET Storefront Website\Embed Links to Videos from socials",
)
VIDEO_JSON = os.path.join(HERE, "videos.json")
FRIENDS_JSON = os.path.join(HERE, "friends.json")
# Change Key Ring Friends prices HERE (cents). Shop buttons read these from /api/friends.
FRIEND_PRICE_SINGLE = 499
FRIEND_PRICE_FIVE = 1999
FRIEND_PRICE_TEN = 3799
FRIENDS_DIR = os.environ.get(
    "MANDMS_FRIENDS_DIR",
    r"C:\Users\Matt\Desktop\MnMs3DPrints\Models\Key Ring Friends",
)
INSTA_RE = re.compile(r"https://www\.instagram\.com/(reel|p|tv)/([A-Za-z0-9_-]+)/")
TIKTOK_RE = re.compile(
    r"https://(?:www\.)?tiktok\.com/@([^/\s\"'<>]+)/video/(\d+)",
    re.I,
)
TIKTOK_ID_RE = re.compile(r'data-video-id=["\'](\d+)["\']', re.I)
_VIDEO_CACHE = {"stamp": None, "data": None}
CHAT_LOCK = threading.Lock()
CHAT_JSON = os.path.join(HERE, "chats.json")
MAX_CHAT_TEXT = 800
MAX_CHAT_NAME = 40
MAX_CHAT_EMAIL = 80
MAX_THREAD_MESSAGES = 40
HIDDEN_STATIC = set(["/chats.json", "/chats.json.tmp"])
CHAT_TO = os.environ.get("MANDMS_CHAT_TO", "mandms3dprints@gmail.com").strip()
FORMSUBMIT_URL = "https://formsubmit.co/ajax/" + CHAT_TO
RECEIPT_TEXT = (
    "Got it. We emailed the bench. Reply comes back to the address you left."
)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_SHIP_TO = 400


def stripe_secret():
    return (
        os.environ.get("STRIPE_SECRET_KEY", "").strip()
        or os.environ.get("STRIPE_API_KEY", "").strip()
    )


def shop_mode():
    if stripe_secret():
        return "live"
    if HOST in ("127.0.0.1", "localhost", "::1"):
        return "demo"
    return "catalog"


def _folder_stamp(src):
    rows = []
    try:
        names = sorted(os.listdir(src))
    except OSError:
        return None
    for name in names:
        if not name.lower().endswith(".txt"):
            continue
        path = os.path.join(src, name)
        try:
            info = os.stat(path)
        except OSError:
            continue
        rows.append((name, int(info.st_mtime), int(info.st_size)))
    return tuple(rows)


def parse_embed_text(text):
    videos = []
    seen = set()
    for match in INSTA_RE.finditer(text or ""):
        kind, code = match.group(1), match.group(2)
        if code in seen:
            continue
        seen.add(code)
        videos.append({
            "id": code,
            "kind": kind,
            "source": "instagram",
            "permalink": "https://www.instagram.com/%s/%s/" % (kind, code),
            "embed": "https://www.instagram.com/%s/%s/embed/" % (kind, code),
        })
    for match in TIKTOK_RE.finditer(text or ""):
        handle, code = match.group(1), match.group(2)
        if code in seen:
            continue
        seen.add(code)
        videos.append({
            "id": code,
            "kind": "video",
            "source": "tiktok",
            "permalink": "https://www.tiktok.com/@%s/video/%s" % (handle, code),
            "embed": "https://www.tiktok.com/player/v1/%s" % code,
        })
    for match in TIKTOK_ID_RE.finditer(text or ""):
        code = match.group(1)
        if code in seen:
            continue
        seen.add(code)
        videos.append({
            "id": code,
            "kind": "video",
            "source": "tiktok",
            "permalink": "https://www.tiktok.com/video/%s" % code,
            "embed": "https://www.tiktok.com/player/v1/%s" % code,
        })
    return videos


def parse_video_folder(src):
    categories = []
    try:
        names = sorted(os.listdir(src))
    except OSError:
        return None
    for name in names:
        if not name.lower().endswith(".txt"):
            continue
        path = os.path.join(src, name)
        try:
            text = open(path, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        videos = parse_embed_text(text)
        label = os.path.splitext(name)[0]
        categories.append({
            "file": name,
            "slug": slugify(label) if label else "category",
            "name": label,
            "count": len(videos),
            "videos": videos,
        })
    return {
        "ok": True,
        "live": True,
        "source": src,
        "importedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": sum(c["count"] for c in categories),
        "categories": categories,
    }


def save_videos(data):
    snap = dict(data)
    snap["ok"] = True
    with open(VIDEO_JSON, "w", encoding="utf-8") as handle:
        json.dump(snap, handle, indent=2)
        handle.write("\n")


def load_videos_snapshot():
    try:
        with open(VIDEO_JSON, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {
            "ok": True,
            "live": False,
            "source": VIDEO_DIR,
            "importedAt": None,
            "total": 0,
            "categories": [],
        }
    data["ok"] = True
    data["live"] = False
    data["total"] = sum(len(c.get("videos") or []) for c in (data.get("categories") or []))
    return data


def load_videos():
    with VIDEO_LOCK:
        stamp = _folder_stamp(VIDEO_DIR) if os.path.isdir(VIDEO_DIR) else None
        if stamp:
            if _VIDEO_CACHE["stamp"] != stamp or _VIDEO_CACHE["data"] is None:
                parsed = parse_video_folder(VIDEO_DIR)
                if parsed is not None:
                    try:
                        save_videos(parsed)
                    except OSError:
                        pass
                    _VIDEO_CACHE["stamp"] = stamp
                    _VIDEO_CACHE["data"] = parsed
            if _VIDEO_CACHE["data"] is not None:
                return _VIDEO_CACHE["data"]
        return load_videos_snapshot()


def pack_cents(qty):
    qty = int(qty or 0)
    if qty == 1:
        return FRIEND_PRICE_SINGLE
    if qty == 5:
        return FRIEND_PRICE_FIVE
    if qty == 10:
        return FRIEND_PRICE_TEN
    return None


def friend_price(qty):
    """Price one pack of the same animal. Only 1, 5, or 10."""
    cents = pack_cents(qty)
    if cents is None:
        return None
    qty = int(qty)
    return {
        "qty": qty,
        "count": qty,
        "total_cents": cents,
        "label": "%s for %s" % (qty, money_usd(cents)),
    }


def money_usd(cents):
    return "$%.2f" % (int(cents) / 100.0)


def friend_price_table():
    packs = []
    for qty in (1, 5, 10):
        cents = pack_cents(qty)
        packs.append({
            "qty": qty,
            "cents": cents,
            "money": money_usd(cents),
            "label": "%s for %s" % (qty, money_usd(cents)),
        })
    return {
        "single_cents": FRIEND_PRICE_SINGLE,
        "five_cents": FRIEND_PRICE_FIVE,
        "ten_cents": FRIEND_PRICE_TEN,
        "single": money_usd(FRIEND_PRICE_SINGLE),
        "five": money_usd(FRIEND_PRICE_FIVE),
        "ten": money_usd(FRIEND_PRICE_TEN),
        "line": " · ".join(p["label"] for p in packs),
        "packs": packs,
    }


def load_friends():
    try:
        with open(FRIENDS_JSON, "r") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {"title": "Key Ring Friends", "lede": "", "price": friend_price_table(), "items": []}
    if not isinstance(data, dict):
        return {"title": "Key Ring Friends", "lede": "", "price": friend_price_table(), "items": []}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        name = (row.get("name") or "").strip()
        folder = os.path.join(FRIENDS_DIR, name) if name else ""
        video = None
        embed_path = os.path.join(folder, "embed.txt") if folder else ""
        if embed_path and os.path.isfile(embed_path):
            try:
                text = open(embed_path, "r", encoding="utf-8", errors="replace").read()
            except OSError:
                text = ""
            parsed = parse_embed_text(text)
            if parsed:
                video = parsed[0]
        if video:
            row["video"] = video
        elif "video" in row:
            del row["video"]
        out.append(row)
    return {
        "title": (data.get("title") or "Key Ring Friends").strip() or "Key Ring Friends",
        "lede": (data.get("lede") or "").strip(),
        "price": friend_price_table(),
        "items": out,
    }


def load_catalog():
    path = os.path.join(HERE, "products.json")
    with open(path, "r") as handle:
        return json.load(handle)


def save_catalog(data):
    path = os.path.join(HERE, "products.json")
    with open(path, "w") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def empty_chats():
    return {"threads": []}


def load_chats():
    try:
        with open(CHAT_JSON, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return empty_chats()
    if not isinstance(data, dict) or not isinstance(data.get("threads"), list):
        return empty_chats()
    return data


def save_chats(data):
    tmp = CHAT_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    os.replace(tmp, CHAT_JSON)


def now_stamp():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def new_id(prefix=""):
    return (prefix + uuid.uuid4().hex[:12]).lower()


def clean_plain(raw, field, maximum):
    text = (raw or "").strip()
    cleaned = []
    for ch in text:
        if ch in ("\n", "\r", "\t"):
            cleaned.append(" ")
        elif ord(ch) >= 32:
            cleaned.append(ch)
    text = re.sub(r" +", " ", "".join(cleaned)).strip()
    if len(text) > maximum:
        raise ValueError(field + " is too long.")
    return text


def clean_chat_text(raw):
    text = clean_plain(raw, "Message", MAX_CHAT_TEXT)
    if not text:
        raise ValueError("Message is required.")
    return text


def clean_chat_email(raw):
    email = clean_plain(raw, "Email", MAX_CHAT_EMAIL)
    if not email:
        raise ValueError("Email is required so we can reply.")
    if not EMAIL_RE.match(email):
        raise ValueError("That email does not look right.")
    return email


def clean_ship_to(raw):
    if isinstance(raw, dict):
        parts = [
            raw.get("line1") or raw.get("street") or "",
            raw.get("line2") or raw.get("apt") or "",
            raw.get("city") or "",
            raw.get("state") or "",
            raw.get("postal_code") or raw.get("zip") or "",
        ]
        raw = ", ".join([str(part).strip() for part in parts if str(part).strip()])
    text = (raw or "").strip()
    cleaned = []
    for ch in text:
        if ch in ("\r", "\t"):
            cleaned.append(" ")
        elif ch == "\n":
            cleaned.append("\n")
        elif ord(ch) >= 32:
            cleaned.append(ch)
    text = re.sub(r"[ ]+", " ", "".join(cleaned))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ValueError("Where it ships is required.")
    if len(text) > MAX_SHIP_TO:
        raise ValueError("Where it ships is too long.")
    return text


def mail_body(name, email, text):
    return (
        "Want what we got? from the MandMs3DPrints shop.\n\n"
        "Name: %s\n"
        "Reply to: %s\n\n"
        "%s\n"
    ) % (name, email, text)


def bag_mail_body(name, email, ship_to, items, total_cents):
    lines = []
    animal_count = 0
    for row in items:
        lines.append("%s — %s (%s)" % (row["name"], row["label"], money_usd(row["cents"])))
        animal_count += int(row["qty"])
    return (
        "Key Ring Friends order from the MandMs3DPrints shop.\n\n"
        "Name: %s\n"
        "Reply to: %s\n"
        "Ship to: %s\n\n"
        "Items (not mix and match; each pack is one animal):\n%s\n\n"
        "Animals: %s\n"
        "Due: %s\n\n"
        "This is an order request, not a paid checkout. Write back with how to pay.\n"
    ) % (
        name,
        email,
        ship_to,
        "\n".join(lines),
        animal_count,
        money_usd(total_cents),
    )


def public_origin(handler):
    proto = (handler.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip()
    host = (handler.headers.get("X-Forwarded-Host") or handler.headers.get("Host") or "").split(",")[0].strip()
    if not host:
        host = "127.0.0.1:%s" % PORT
    if not proto:
        proto = "https" if HOST not in LOCAL_HOSTS else "http"
    return "%s://%s" % (proto, host)


def stripe_checkout_session(packed, total_cents, email, name, ship_to, origin):
    secret = stripe_secret()
    if not secret:
        return None, "Connect Stripe in ABILITIES, then set STRIPE_SECRET_KEY on the shop host."
    fields = [
        ("mode", "payment"),
        ("success_url", origin.rstrip("/") + "/?paid=1"),
        ("cancel_url", origin.rstrip("/") + "/#mm-bag"),
        ("customer_email", email),
        ("billing_address_collection", "required"),
        ("payment_intent_data[description]", "Key Ring Friends — MandMs3DPrints"),
        ("payment_intent_data[metadata][shop]", "mandms3dprints"),
        ("payment_intent_data[metadata][name]", name[:80]),
        ("payment_intent_data[metadata][ship_to]", ship_to[:400]),
        ("metadata[shop]", "mandms3dprints"),
        ("metadata[name]", name[:80]),
        ("metadata[email]", email[:80]),
        ("metadata[ship_to]", ship_to[:400]),
        ("metadata[total_cents]", str(total_cents)),
    ]
    for i, row in enumerate(packed):
        prefix = "line_items[%s]" % i
        fields.append((prefix + "[quantity]", "1"))
        fields.append((prefix + "[price_data][currency]", "usd"))
        fields.append((prefix + "[price_data][unit_amount]", str(row["cents"])))
        fields.append((prefix + "[price_data][product_data][name]", "Key Ring Friend — %s" % row["name"]))
        fields.append((prefix + "[price_data][product_data][description]", "%s. Same animal only." % row["label"]))
        fields.append((prefix + "[price_data][product_data][metadata][friend_id]", row["id"]))
        fields.append((prefix + "[price_data][product_data][metadata][qty]", str(row["qty"])))
    body = urlencode(fields).encode("utf-8")
    req = Request(STRIPE_CHECKOUT_URL, data=body, method="POST")
    req.add_header("Authorization", "Bearer " + secret)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Idempotency-Key", "mm-bag-" + uuid.uuid4().hex)
    try:
        handle = urlopen(req, timeout=20)
        raw = handle.read()
        handle.close()
    except HTTPError as err:
        try:
            raw = err.read()
        except Exception:
            raw = b""
        try:
            data = json.loads(raw.decode("utf-8") if raw else "{}")
        except ValueError:
            data = {}
        message = ((data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else None) or (
            "Stripe said %s." % err.code
        )
        return None, message
    except URLError:
        return None, "Could not reach Stripe."
    except Exception:
        return None, "Stripe checkout failed."
    try:
        data = json.loads(raw.decode("utf-8") if raw else "{}")
    except ValueError:
        return None, "Stripe sent a bad reply."
    url = data.get("url")
    if not url:
        return None, "Stripe did not return a checkout URL."
    return data, None


def email_bench(name, email, text, referer="http://127.0.0.1:8791/", subject=None):
    """Send the visitor note to Gmail from the shop host. StarNet is not in this path."""
    try:
        from urllib.parse import urlencode
    except ImportError:
        from urllib import urlencode
    origin = (referer or "http://127.0.0.1:8791/").rstrip("/")
    if origin.endswith("/"):
        origin = origin[:-1]
    payload = urlencode({
        "name": name,
        "email": email,
        "_replyto": email,
        "_subject": subject or ("Want what we got? from %s" % name),
        "message": text if subject else mail_body(name, email, text),
        "_template": "box",
        "_captcha": "false",
    }).encode("utf-8")
    req = Request(
        FORMSUBMIT_URL,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 MandMs3DPrints-shop/1.0",
            "Referer": referer or "http://127.0.0.1:8791/",
            "Origin": origin or "http://127.0.0.1:8791",
        },
    )
    try:
        handle = urlopen(req, timeout=12)
        raw = handle.read()
        handle.close()
    except HTTPError as err:
        try:
            raw = err.read()
        except Exception:
            raw = b""
        if err.code in (200, 201, 202):
            return True, "sent"
        return False, "Mail host said %s." % err.code
    except URLError:
        return False, "Could not reach the mail host."
    except Exception:
        return False, "Mail send failed."
    try:
        data = json.loads(raw.decode("utf-8") if raw else "{}")
    except ValueError:
        data = {}
    success = str((data or {}).get("success") or "").lower()
    if success in ("true", "1"):
        return True, "sent"
    message = (data or {}).get("message") or ""
    if "confirm" in message.lower() or "activation" in message.lower():
        return True, "confirm"
    return False, message or "Mail host did not accept the note."


def public_messages(thread):
    out = []
    for msg in thread.get("messages") or []:
        role = msg.get("from")
        if role not in ("visitor", "bench", "receipt"):
            continue
        out.append({
            "id": msg.get("id"),
            "from": role,
            "text": msg.get("text") or "",
            "at": msg.get("at"),
        })
    return out


def public_thread(thread):
    return {
        "ok": True,
        "id": thread.get("id"),
        "token": thread.get("token"),
        "name": thread.get("name") or "Visitor",
        "createdAt": thread.get("createdAt"),
        "updatedAt": thread.get("updatedAt"),
        "messages": public_messages(thread),
    }


def bench_thread(thread):
    preview = ""
    pending = 0
    for msg in thread.get("messages") or []:
        if msg.get("from") == "visitor":
            preview = msg.get("text") or preview
            if not msg.get("pinged"):
                pending += 1
    return {
        "id": thread.get("id"),
        "name": thread.get("name") or "Visitor",
        "email": thread.get("email") or "",
        "createdAt": thread.get("createdAt"),
        "updatedAt": thread.get("updatedAt"),
        "pending": pending,
        "preview": preview,
        "messages": [
            {
                "id": msg.get("id"),
                "from": msg.get("from"),
                "text": msg.get("text") or "",
                "at": msg.get("at"),
                "pinged": bool(msg.get("pinged")),
            }
            for msg in (thread.get("messages") or [])
        ],
    }


def find_thread(chats, token=None, tid=None):
    for thread in chats.get("threads") or []:
        if token and thread.get("token") == token:
            return thread
        if tid and thread.get("id") == tid:
            return thread
    return None


def pending_visitor_messages(chats):
    rows = []
    for thread in chats.get("threads") or []:
        for msg in thread.get("messages") or []:
            if msg.get("from") != "visitor" or msg.get("pinged"):
                continue
            rows.append({
                "threadId": thread.get("id"),
                "messageId": msg.get("id"),
                "name": thread.get("name") or "Visitor",
                "text": msg.get("text") or "",
                "at": msg.get("at"),
            })
    return rows


def client_host(handler):
    host = ""
    if handler.client_address:
        host = handler.client_address[0] or ""
    host = host.split("%")[0].strip().lower()
    if host.startswith("::ffff:"):
        host = host[7:]
    return host


def is_local_client(handler):
    return client_host(handler) in LOCAL_HOSTS


def slugify(name):
    raw = (name or "").strip().lower()
    out = []
    prev_dash = False
    for ch in raw:
        ok = ("a" <= ch <= "z") or ("0" <= ch <= "9")
        if ok:
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    slug = "".join(out).strip("-")
    return slug or "part"


def as_int(value, field, minimum=0):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(field + " must be a whole number.")
    if number < minimum:
        raise ValueError(field + " cannot be negative.")
    return number


def clean_product(raw, fallback_id=None):
    if not isinstance(raw, dict):
        raise ValueError("Part data is missing.")
    name = (raw.get("name") or "").strip()
    if not name:
        raise ValueError("Name is required.")
    pid = (raw.get("id") or fallback_id or slugify(name)).strip().lower()
    pid = slugify(pid)
    if not pid:
        raise ValueError("Part id is required.")
    specs_in = raw.get("specs") if isinstance(raw.get("specs"), dict) else {}
    hidden = raw.get("hidden")
    if hidden in ("false", "0", "off", "", None):
        hidden = False
    return {
        "id": pid,
        "name": name,
        "price": as_int(raw.get("price"), "Price"),
        "kind": "physical",
        "stock": as_int(raw.get("stock"), "Stock"),
        "summary": (raw.get("summary") or "").strip(),
        "hidden": bool(hidden),
        "specs": {
            "size": (specs_in.get("size") or "").strip(),
            "layer": (specs_in.get("layer") or "").strip() or "0.2 mm",
            "filament": (specs_in.get("filament") or "").strip(),
            "time": (specs_in.get("time") or "").strip(),
        },
    }


def public_catalog():
    cat = load_catalog()
    visible = [p for p in cat.get("products", []) if not p.get("hidden")]
    out = dict(cat)
    out["products"] = visible
    return out


def apply_store_patch(cat, store_in):
    if not isinstance(store_in, dict):
        return
    store = cat.setdefault("store", {})
    if "tagline" in store_in:
        store["tagline"] = (store_in.get("tagline") or "").strip()
    ship_in = store_in.get("shipping")
    if isinstance(ship_in, dict):
        ship = store.setdefault("shipping", {})
        if "amount" in ship_in:
            ship["amount"] = as_int(ship_in.get("amount"), "Shipping")
        if "label" in ship_in:
            ship["label"] = (ship_in.get("label") or "").strip() or ship.get("label") or "USPS Ground Advantage"


class ShopHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        try:
            SimpleHTTPRequestHandler.__init__(self, *args, directory=HERE, **kwargs)
        except TypeError:
            SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)

    def translate_path(self, path):
        result = SimpleHTTPRequestHandler.translate_path(self, path)
        shop_root = os.path.abspath(HERE)
        if not os.path.abspath(result).startswith(shop_root):
            return os.path.join(shop_root, "index.html")
        return result

    def log_message(self, fmt, *args):
        sys.stderr.write("[mandms3dprints] %s\n" % (fmt % args))

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            payload = json.loads(raw or "{}")
        except ValueError:
            raise ValueError("Bad JSON.")
        if not isinstance(payload, dict):
            raise ValueError("Expected an object.")
        return payload

    def _require_local(self):
        if is_local_client(self):
            return True
        self._json({
            "ok": False,
            "error": "The bench only writes from this machine. Open http://127.0.0.1:%s/bench.html" % PORT,
        }, 403)
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in HIDDEN_STATIC:
            self.send_error(404)
            return
        if path == "/api/health":
            cat = load_catalog()
            ship = cat.get("store", {}).get("shipping", {})
            return self._json({
                "ok": True,
                "kind": "physical",
                "mode": shop_mode(),
                "stripe": bool(stripe_secret()),
                "shipping_usd": ship.get("amount", 8),
                "shipping_label": ship.get("label", "USPS Ground Advantage"),
                "bench": is_local_client(self),
            })
        if path == "/api/products":
            return self._json(public_catalog())
        if path == "/api/videos":
            return self._json(load_videos())
        if path == "/api/friends":
            return self._json(load_friends())
        if path == "/api/chat":
            return self._handle_chat_get(parse_qs(parsed.query or ""))
        if path == "/api/bench":
            if not self._require_local():
                return
            cat = load_catalog()
            return self._json({
                "ok": True,
                "writable": True,
                "store": cat.get("store") or {},
                "products": cat.get("products") or [],
            })
        if path == "/api/bench/chats":
            return self._handle_bench_chats_get()
        if path == "/api/bench/chat/pending":
            return self._handle_chat_pending()
        if path == "/api/order":
            query = parse_qs(parsed.query or "")
            session_id = (query.get("session_id") or [""])[0]
            for order in ORDERS:
                if order.get("id") == session_id:
                    return self._json({"ok": True, "order": order})
            return self._json({"ok": False, "error": "Order not found."}, 404)
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/api/bench", "/api/bench/product", "/api/bench/delete"):
            return self._handle_bench(path)
        if path == "/api/chat":
            return self._handle_chat_post()
        if path == "/api/bag":
            return self._handle_bag_post()
        if path == "/api/bench/chat":
            return self._handle_bench_chat_reply()
        if path == "/api/bench/chat/pinged":
            return self._handle_chat_pinged()
        if path == "/api/bench/chat/delete":
            return self._handle_bench_chat_delete()
        if path != "/api/checkout":
            self.send_error(404)
            return
        if not stripe_secret():
            return self._json({
                "ok": False,
                "error": "Checkout is not live yet. Connect Stripe, then set STRIPE_SECRET_KEY on the host.",
            }, 503)
        try:
            payload = self._read_json()
        except ValueError as err:
            return self._json({"ok": False, "error": str(err)}, 400)

        with CATALOG_LOCK:
            cat = load_catalog()
            products = dict((p["id"], p) for p in cat.get("products", []))
            items_in = payload.get("items") or []
            if not items_in:
                return self._json({"ok": False, "error": "Bag is empty."}, 400)

            packed = []
            pack_list = []
            subtotal = 0
            for row in items_in:
                pid = row.get("id")
                try:
                    qty = int(row.get("qty") or 0)
                except (TypeError, ValueError):
                    return self._json({"ok": False, "error": "Bad quantity."}, 400)
                part = products.get(pid)
                if not part or part.get("hidden") or qty < 1:
                    return self._json({"ok": False, "error": "Unknown part."}, 400)
                stock = int(part.get("stock") or 0)
                if qty > stock:
                    return self._json({
                        "ok": False,
                        "error": part["name"] + " only has " + str(stock) + " on the bench.",
                    }, 400)
                part["stock"] = stock - qty
                packed.append({
                    "id": pid,
                    "name": part["name"],
                    "qty": qty,
                    "price": part["price"],
                })
                pack_list.append(str(qty) + "x " + part["name"])
                subtotal += int(part["price"]) * qty

            ship = cat.get("store", {}).get("shipping", {})
            ship_amt = int(ship.get("amount") or 0) if packed else 0
            save_catalog(cat)

        ship_to = payload.get("ship_to") or {}
        order = {
            "id": "MM-" + uuid.uuid4().hex[:8].upper(),
            "mode": "demo",
            "total": subtotal + ship_amt,
            "subtotal": subtotal,
            "shipping": ship_amt,
            "items": packed,
            "pack_list": pack_list,
            "ship_to": ship_to,
            "name": payload.get("name") or ship_to.get("name") or "",
            "email": payload.get("email") or "",
            "at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        ORDERS.append(order)
        return self._json({"ok": True, "order": order})

    def _handle_chat_get(self, query):
        token = (query.get("token") or [""])[0].strip().lower()
        if not token:
            return self._json({"ok": False, "error": "Chat token is required."}, 400)
        with CHAT_LOCK:
            thread = find_thread(load_chats(), token=token)
            if thread is None:
                return self._json({"ok": False, "error": "Chat not found."}, 404)
            return self._json(public_thread(thread))

    def _handle_bag_post(self):
        try:
            payload = self._read_json()
            name = clean_plain(payload.get("name"), "Name", MAX_CHAT_NAME) or "Visitor"
            email = clean_chat_email(payload.get("email"))
            ship_to = clean_ship_to(payload.get("ship_to") or payload.get("shipping"))
            items_in = payload.get("items") or []
            if not isinstance(items_in, list) or not items_in:
                raise ValueError("Bag is empty.")
        except ValueError as err:
            return self._json({"ok": False, "error": str(err)}, 400)

        friends = dict((row.get("id"), row) for row in load_friends().get("items") or [])
        packed = []
        total_cents = 0
        seen = set()
        for row in items_in:
            if not isinstance(row, dict):
                return self._json({"ok": False, "error": "Bad bag line."}, 400)
            pid = (row.get("id") or "").strip()
            try:
                qty = int(row.get("qty") or 0)
            except (TypeError, ValueError):
                return self._json({"ok": False, "error": "Bad quantity."}, 400)
            friend = friends.get(pid)
            deal = friend_price(qty)
            if not friend or deal is None or pid in seen:
                return self._json({
                    "ok": False,
                    "error": "Each Key Ring Friend is 1, 5, or 10 of that same animal. Not mix and match.",
                }, 400)
            seen.add(pid)
            packed.append({
                "id": pid,
                "name": friend.get("name") or pid,
                "qty": qty,
                "cents": deal["total_cents"],
                "label": deal["label"],
            })
            total_cents += deal["total_cents"]

        session, err = stripe_checkout_session(
            packed,
            total_cents,
            email,
            name,
            ship_to,
            public_origin(self),
        )
        if err or not session:
            return self._json({
                "ok": False,
                "error": err or "Could not start Stripe checkout.",
            }, 503)
        return self._json({
            "ok": True,
            "checkout_url": session.get("url"),
            "session_id": session.get("id"),
            "count": sum(row["qty"] for row in packed),
            "total": money_usd(total_cents),
            "items": packed,
        })

    def _handle_chat_post(self):
        try:
            payload = self._read_json()
            text = clean_chat_text(payload.get("text"))
            name = clean_plain(payload.get("name"), "Name", MAX_CHAT_NAME) or "Visitor"
            email = clean_chat_email(payload.get("email"))
            token = (payload.get("token") or "").strip().lower()
        except ValueError as err:
            return self._json({"ok": False, "error": str(err)}, 400)

        referer = self.headers.get("Referer") or self.headers.get("Origin") or ""
        mailed, mail_note = email_bench(name, email, text, referer=referer)
        if not mailed:
            return self._json({
                "ok": False,
                "error": mail_note or "Could not email the bench. Instagram is @mandms3dprints if this box dies.",
            }, 502)

        with CHAT_LOCK:
            chats = load_chats()
            thread = find_thread(chats, token=token) if token else None
            stamp = now_stamp()
            visitor_msg = {
                "id": new_id("m"),
                "from": "visitor",
                "text": text,
                "at": stamp,
                "pinged": True,
                "mailed": True,
            }
            receipt_text = RECEIPT_TEXT
            if mail_note == "confirm":
                receipt_text = (
                    "Got it. First note from this shop needs Matt to tap Confirm in Gmail. "
                    "After that, replies come back to the address you left."
                )
            if thread is None:
                thread = {
                    "id": new_id("t"),
                    "token": uuid.uuid4().hex,
                    "name": name,
                    "email": email,
                    "createdAt": stamp,
                    "updatedAt": stamp,
                    "messages": [
                        visitor_msg,
                        {
                            "id": new_id("m"),
                            "from": "receipt",
                            "text": receipt_text,
                            "at": stamp,
                            "pinged": True,
                        },
                    ],
                }
                chats.setdefault("threads", []).append(thread)
            else:
                messages = thread.setdefault("messages", [])
                if len(messages) >= MAX_THREAD_MESSAGES:
                    return self._json({
                        "ok": False,
                        "error": "This chat is full. Start a new one from the bubble if you still need us.",
                    }, 400)
                if name and name != "Visitor":
                    thread["name"] = name
                thread["email"] = email
                messages.append(visitor_msg)
                thread["updatedAt"] = stamp
            save_chats(chats)
            return self._json(public_thread(thread))

    def _handle_bench_chats_get(self):
        if not self._require_local():
            return
        with CHAT_LOCK:
            chats = load_chats()
            threads = [bench_thread(t) for t in (chats.get("threads") or [])]
            threads.sort(key=lambda row: row.get("updatedAt") or "", reverse=True)
            return self._json({
                "ok": True,
                "count": len(threads),
                "pending": sum(t.get("pending") or 0 for t in threads),
                "threads": threads,
            })

    def _handle_chat_pending(self):
        if not self._require_local():
            return
        with CHAT_LOCK:
            pending = pending_visitor_messages(load_chats())
            return self._json({
                "ok": True,
                "count": len(pending),
                "messages": pending,
            })

    def _handle_bench_chat_reply(self):
        if not self._require_local():
            return
        try:
            payload = self._read_json()
            tid = (payload.get("id") or "").strip().lower()
            text = clean_chat_text(payload.get("text"))
            if not tid:
                raise ValueError("Chat id is required.")
        except ValueError as err:
            return self._json({"ok": False, "error": str(err)}, 400)
        with CHAT_LOCK:
            chats = load_chats()
            thread = find_thread(chats, tid=tid)
            if thread is None:
                return self._json({"ok": False, "error": "Chat not found."}, 404)
            messages = thread.setdefault("messages", [])
            if len(messages) >= MAX_THREAD_MESSAGES:
                return self._json({"ok": False, "error": "This chat is full."}, 400)
            stamp = now_stamp()
            messages.append({
                "id": new_id("m"),
                "from": "bench",
                "text": text,
                "at": stamp,
                "pinged": True,
            })
            thread["updatedAt"] = stamp
            save_chats(chats)
            return self._json({"ok": True, "thread": bench_thread(thread)})

    def _handle_chat_pinged(self):
        if not self._require_local():
            return
        try:
            payload = self._read_json()
        except ValueError as err:
            return self._json({"ok": False, "error": str(err)}, 400)
        ids = payload.get("messageIds") or payload.get("ids") or []
        if not isinstance(ids, list):
            return self._json({"ok": False, "error": "messageIds must be a list."}, 400)
        wanted = set([str(i).strip().lower() for i in ids if str(i).strip()])
        marked = 0
        with CHAT_LOCK:
            chats = load_chats()
            for thread in chats.get("threads") or []:
                for msg in thread.get("messages") or []:
                    if msg.get("id") in wanted and msg.get("from") == "visitor":
                        if not msg.get("pinged"):
                            marked += 1
                        msg["pinged"] = True
            if marked:
                save_chats(chats)
            pending = pending_visitor_messages(chats)
            return self._json({"ok": True, "marked": marked, "pending": len(pending)})

    def _handle_bench_chat_delete(self):
        if not self._require_local():
            return
        try:
            payload = self._read_json()
            tid = (payload.get("id") or "").strip().lower()
            if not tid:
                raise ValueError("Chat id is required.")
        except ValueError as err:
            return self._json({"ok": False, "error": str(err)}, 400)
        with CHAT_LOCK:
            chats = load_chats()
            threads = chats.get("threads") or []
            next_threads = [t for t in threads if t.get("id") != tid]
            if len(next_threads) == len(threads):
                return self._json({"ok": False, "error": "Chat not found."}, 404)
            chats["threads"] = next_threads
            save_chats(chats)
            return self._json({"ok": True, "removed": tid, "count": len(next_threads)})

    def _handle_bench(self, path):
        if not self._require_local():
            return
        try:
            payload = self._read_json()
        except ValueError as err:
            return self._json({"ok": False, "error": str(err)}, 400)

        try:
            with CATALOG_LOCK:
                cat = load_catalog()
                products = list(cat.get("products") or [])

                if path == "/api/bench":
                    if "products" in payload:
                        cleaned = [clean_product(row) for row in (payload.get("products") or [])]
                        seen = set()
                        for part in cleaned:
                            if part["id"] in seen:
                                raise ValueError("Two parts share the id " + part["id"] + ".")
                            seen.add(part["id"])
                        products = cleaned
                    apply_store_patch(cat, payload.get("store"))
                    cat["products"] = products
                    save_catalog(cat)
                    return self._json({
                        "ok": True,
                        "store": cat.get("store") or {},
                        "products": cat.get("products") or [],
                    })

                if path == "/api/bench/delete":
                    pid = slugify(payload.get("id") or "")
                    if not pid:
                        raise ValueError("Part id is required.")
                    next_products = [p for p in products if p.get("id") != pid]
                    if len(next_products) == len(products):
                        return self._json({"ok": False, "error": "Unknown part."}, 404)
                    cat["products"] = next_products
                    save_catalog(cat)
                    return self._json({
                        "ok": True,
                        "removed": pid,
                        "products": cat["products"],
                    })

                # /api/bench/product — upsert one printed part
                existing = None
                requested_id = slugify(payload.get("id") or "")
                if requested_id:
                    for part in products:
                        if part.get("id") == requested_id:
                            existing = part
                            break
                cleaned = clean_product(payload, requested_id or None)
                if existing is None:
                    for part in products:
                        if part.get("id") == cleaned["id"]:
                            raise ValueError("A part with that id already exists.")
                    products.append(cleaned)
                else:
                    next_products = []
                    for part in products:
                        if part.get("id") == existing.get("id"):
                            next_products.append(cleaned)
                        else:
                            next_products.append(part)
                    products = next_products
                cat["products"] = products
                save_catalog(cat)
                return self._json({"ok": True, "product": cleaned, "products": products})
        except ValueError as err:
            return self._json({"ok": False, "error": str(err)}, 400)


def main():
    os.chdir(HERE)
    server = ThreadingHTTPServer((HOST, PORT), ShopHandler)
    print("MandMs3DPrints owned shop on http://%s:%s/  mode=%s" % (HOST, PORT, shop_mode()))
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    main()
