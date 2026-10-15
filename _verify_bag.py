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


def post(items):
    data = json.dumps(
        {
            "name": "Verify",
            "email": "verify@example.com",
            "ship_to": "123 Test St",
            "items": items,
        }
    ).encode("utf-8")
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
    check("send-order", "Send this order" in html)
    check("send-email", "Send email" in html)
    check("form-line", "Enter your email and tell us what you need below" in html)
    check("no-eleven-copy", "eleven" not in html.lower())

    code, payload = post([{"id": "bronco", "qty": 11}])
    check("api-qty11", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 6}])
    check("api-qty6", code == 400, payload.get("error") if isinstance(payload, dict) else payload)
    code, payload = post([{"id": "bronco", "qty": 1}, {"id": "bronco", "qty": 5}])
    check("api-dup", code == 400, payload.get("error") if isinstance(payload, dict) else payload)

    print("OVERALL", "PASS" if all(results) else "FAIL")


if __name__ == "__main__":
    main()
