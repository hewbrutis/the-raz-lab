# Local pack-rule check. Does not POST successful orders (that emails the bench).
from __future__ import print_function
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import server

URL = "http://127.0.0.1:8791/api/bag"


def post(items, extra=None):
    payload = {
        "name": "Verify",
        "email": "verify@example.com",
        "ship_to": "123 Test St, Austin, TX 78701",
        "items": items,
    }
    if extra:
        payload.update(extra)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = {"raw": raw}
        return err.code, parsed


def main():
    results = []

    def check(name, ok, extra=""):
        print("%s %s %s" % (name, "PASS" if ok else "FAIL", extra))
        results.append(ok)

    check("cents-1", server.pack_cents(1) == 499, "499")
    check("cents-5", server.pack_cents(5) == 1999, "1999")
    check("cents-10", server.pack_cents(10) == 3799, "3799")
    check("cents-11", server.pack_cents(11) is None, "None")
    check("cents-6", server.pack_cents(6) is None, "None")
    check("mix-math", server.pack_cents(5) + server.pack_cents(1) == 2498, "2498")

    friends = server.load_friends()
    names = [row.get("name") for row in friends.get("items") or []]
    check("six-friends", len(names) == 6, ",".join(names))

    html = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    check("pack-buttons", all(x in html for x in ['data-pack="1"', 'data-pack="5"', 'data-pack="10"']))
    check("no-add-to-bag", "Add to bag" not in html)
    check("not-mix", "Not mix and match" in html)
    check("pay-now", "Pay now" in html)
    check("send-email", "Send email" in html)
    check("form-line", "Enter your email and tell us what you need below" in html)
    check("no-eleven-copy", "eleven" not in html.lower())
    check("ship-box", 'id="bag-ship"' in html and "Where it ships" in html)
    check("no-ship-form", 'id="bag-line1"' not in html and 'id="bag-city"' not in html and 'id="bag-zip"' not in html)
    src = open(os.path.join(HERE, "server.py"), encoding="utf-8").read()
    check("no-stripe-ship-form", "shipping_address_collection" not in src)
    check("ship-to-meta", 'metadata[ship_to]' in src)

    addr = server.clean_ship_to("123 Test St\nAustin, TX 78701")
    check("addr-ok", "123 Test St" in addr and "Austin, TX 78701" in addr, addr)
    missing = None
    try:
        server.clean_ship_to("   ")
    except ValueError as err:
        missing = str(err)
    check("addr-empty-rejected", missing == "Where it ships is required.", missing)
    joined = server.clean_ship_to({
        "line1": "123 Test St",
        "city": "Austin",
        "state": "TX",
        "postal_code": "78701",
    })
    check("addr-dict-joined", "123 Test St" in joined and "Austin" in joined, joined)

    code, payload = post([{"id": "bronco", "qty": 11}])
    check("api-qty11", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 6}])
    check("api-qty6", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 1}, {"id": "bronco", "qty": 5}])
    check("api-dup", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 1}], extra={"ship_to": ""})
    check("api-no-ship", code == 400, payload.get("error") if isinstance(payload, dict) else payload)

    print("OVERALL", "PASS" if all(results) else "FAIL")


if __name__ == "__main__":
    main()
