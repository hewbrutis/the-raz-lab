# The Raz LAB

Printed parts from the bench. MandMs3DPrints (Matt and Misti's 3D Prints). No marketplace cut.

This repo is the public shop: a Python server (`server.py`), a dark storefront (`index.html`), and Key Ring Friends packs of 1, 5, or 10. Checkout is Stripe. Fulfillment is packing a box, not an STL download.

Not forge-files. That name is retired.

## Run locally

```
python -u server.py
```

Then open http://127.0.0.1:8791/

No Stripe key = Pay now cannot charge. Connect Stripe, then set `STRIPE_SECRET_KEY` on the host.

## Deploy (Render)

This is a Python web service, not a static site.

1. Render → New → Web Service → this repo (`hewbrutis/the-raz-lab`)
2. Build: `true`
3. Start: `python -u server.py`
4. Health: `/api/health`
5. Env vars (set in Render, never in git):
   - `STRIPE_SECRET_KEY`
   - `PUBLIC_BASE_URL`

`render.yaml` names the service `mandms3dprints`.

## Do not commit

- `.env` / Stripe keys
- `chats.json` (visitor emails)
- `data/orders.json`
- `files/*.stl`
