# MandMs3DPrints storefront — owned by KIKI

Taken over from ZERO on 2026-10-09.

Who the page is for: a visitor who found MandMs3DPrints from Matt and Misti's 3D-print content.
One action: read the lab intro, then watch the prints in grouped carousels.
Public title stack: The Raz LAB / by / MandMs3DPrints - (Matt and Misti's 3D Prints).
Wanted host: https://mandms3dprints.onrender.com/

This folder is the public storefront. Pages stay yours. Not Webflow, not a rented builder.

Go-live path: shop/GO_LIVE.md
- Host is Render. Keep that path.
- Local review: http://127.0.0.1:8791/
- If a cloud host sets PORT, the server binds 0.0.0.0.
- Key Ring Friends Pay now uses Stripe Checkout. Connect Stripe in ABILITIES, then set STRIPE_SECRET_KEY on Render.

From the printer gallery: GET /api/videos — Instagram and TikTok embeds from Desktop\StarNet Trusted\STARNET Storefront Website\Embed Links to Videos from socials. Details in shop/VIDEOS.md.
Local inventory editor (this machine only): http://127.0.0.1:8791/bench.html
- GET/POST /api/bench, POST /api/bench/product, POST /api/bench/delete
- Writes products.json. Hidden parts stay on the bench and drop off the public catalog.
- Non-local clients get 403. Do not publish /bench.html as the storefront.

Shop contact (buyers never see Discord):
- Public bubble on index.html — Want what we got?
- Visitor leaves an email. The shop emails mandms3dprints@gmail.com. Reply in Gmail.
- StarNet is not required for this path. Details: shop/CHAT.md
