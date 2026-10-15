import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8791"


def get(path):
    with urlopen(BASE + path) as handle:
        return json.load(handle)


def post(path, body):
    req = Request(
        BASE + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req) as handle:
            return handle.status, json.load(handle)
    except HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


orig = get("/api/bench")
print("orig_count", len(orig["products"]), [p["id"] for p in orig["products"]])

st, added = post("/api/bench/product", {
    "id": "probe-jig",
    "name": "Probe Bench Jig",
    "price": 11,
    "stock": 4,
    "summary": "Temporary verification part. Not for sale.",
    "specs": {
        "size": "40 x 20 x 8 mm",
        "layer": "0.2 mm",
        "filament": "~6 g PLA",
        "time": "~25 min",
    },
})
print("add", st, added.get("ok"), [p["id"] for p in added.get("products", [])])
print("public_after_add", [p["id"] for p in get("/api/products")["products"]])

st, hid = post("/api/bench/product", {
    "id": "probe-jig",
    "name": "Probe Bench Jig",
    "price": 11,
    "stock": 4,
    "hidden": True,
    "summary": "Temporary verification part. Not for sale.",
    "specs": {"size": "40 x 20 x 8 mm"},
})
print("hide", st, hid.get("ok"), hid.get("product", {}).get("hidden"))
print("public_after_hide", [p["id"] for p in get("/api/products")["products"]])

st, stock = post("/api/bench/product", {
    "id": "cable-clip",
    "name": "Desk Cable Clip",
    "price": 9,
    "stock": 5,
    "summary": "Printed U-clip that snaps over a desk edge and keeps one cable from wandering.",
    "specs": {
        "size": "24 x 12 x 18 mm",
        "layer": "0.2 mm",
        "filament": "~4 g PLA",
        "time": "~20 min",
    },
})
print("clip_stock", st, [p["stock"] for p in stock.get("products", []) if p["id"] == "cable-clip"])

st, gone = post("/api/bench/delete", {"id": "probe-jig"})
print("delete_probe", st, gone.get("ok"), [p["id"] for p in gone.get("products", [])])

st, rest = post("/api/bench", {"store": orig["store"], "products": orig["products"]})
print("restore", st, rest.get("ok"), [(p["id"], p["stock"], bool(p.get("hidden"))) for p in rest.get("products", [])])
print("public_final", [(p["id"], p["stock"]) for p in get("/api/products")["products"]])
