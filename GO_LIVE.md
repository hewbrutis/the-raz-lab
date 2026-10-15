# MandMs3DPrints — how this shop goes live

Not Webflow. Not Squarespace. Not Shopify. Not Railway. The pages stay in this folder.

Wanted public URL: `https://mandms3dprints.onrender.com/`
The GitHub repo for this shop is `hewbrutis/the-raz-lab` — not forge-files.

## Host
Render Python web service. Not a static site.
- New Web Service from this repo: `hewbrutis/the-raz-lab`
- Build: `true`
- Start: `python -u server.py`
- Health: `/api/health`
- Env: `STRIPE_SECRET_KEY` and `PUBLIC_BASE_URL` in Render, never git
- `render.yaml` names the service `mandms3dprints`

No Stripe key = Pay now cannot charge. Connect Stripe, then set `STRIPE_SECRET_KEY` on the host.
