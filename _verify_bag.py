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
        "shipping": {
            "line1": "123 Test St",
            "city": "Austin",
            "state": "TX",
            "postal_code": "78701",
        },
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
    check("ship-form", 'id="bag-line1"' in html and 'id="bag-city"' in html and 'id="bag-state"' in html and 'id="bag-zip"' in html)
    check("ship-required-copy", "We cannot ship a Key Ring Friend without a US street address" in html)
    check("no-old-ship-box", 'id="bag-ship"' not in html)
    check("stripe-ship", 'shipping_address_collection[allowed_countries][0]' in open(os.path.join(HERE, "server.py"), encoding="utf-8").read())

    addr = server.clean_shipping_address({
        "line1": "123 Test St",
        "city": "Austin",
        "state": "tx",
        "postal_code": "78701",
    })
    check("addr-ok", addr["state"] == "TX" and addr["country"] == "US", addr["state"])
    check("addr-format", "123 Test St" in server.format_ship_to(addr) and "Austin, TX 78701" in server.format_ship_to(addr))
    missing = None
    try:
        server.clean_shipping_address("123 Test St")
    except ValueError as err:
        missing = str(err)
    check("addr-string-rejected", missing == "Shipping address is required.", missing)
    missing = None
    try:
        server.clean_shipping_address({"line1": "123 Test St", "city": "Austin", "state": "TX"})
    except ValueError as err:
        missing = str(err)
    check("addr-zip-required", missing == "ZIP must be 5 digits.", missing)

    code, payload = post([{"id": "bronco", "qty": 11}])
    check("api-qty11", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 6}])
    check("api-qty6", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 1}, {"id": "bronco", "qty": 5}])
    check("api-dup", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 1}], extra={"shipping": {}})
    check("api-no-ship", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 1}], extra={"shipping": "123 Test St"})
    check("api-ship-string", code == 400, payload.get("error") if isinstance(payload, dict) else payload)

    print("OVERALL", "PASS" if all(results) else "FAIL")


if __name__ == "__main__":
    main()
