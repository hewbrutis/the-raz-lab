from __future__ import print_function
import json
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8799/api/bag"


def post(items, extra=None):
    payload = {
        "name": "Verify",
        "email": "verify@example.com",
        "ship_to": "123 Test St, Austin, TX 78701",
        "items": items,
    }
    if extra is not None:
        payload.update(extra)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = {"raw": raw}
        return err.code, parsed


def main():
    cases = [
        ("qty11", [{"id": "bronco", "qty": 11}], None, 400),
        ("qty6", [{"id": "bronco", "qty": 6}], None, 400),
        ("dup", [{"id": "bronco", "qty": 1}, {"id": "bronco", "qty": 5}], None, 400),
        ("no-ship", [{"id": "bronco", "qty": 1}], {"ship_to": ""}, 400),
        ("ok-then-stripe", [{"id": "bronco", "qty": 1}], None, 503),
    ]
    ok = True
    for name, items, extra, expect in cases:
        code, payload = post(items, extra)
        err = payload.get("error") if isinstance(payload, dict) else payload
        passed = code == expect
        if name.startswith("no-ship") or name.startswith("ship-string"):
            passed = passed and "required" in str(err).lower() or "street" in str(err).lower() or "shipping" in str(err).lower() or "zip" in str(err).lower()
        print("%s %s %s %s" % (name, "PASS" if code == expect else "FAIL", code, err))
        if code != expect:
            ok = False
    print("OVERALL", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
