# MandMs3DPrints - local vs live (checked 2026-10-11)

Who: Commander deciding whether to push the current Raz LAB page.
One action: know what survives a push, and what would change.

This is a comparison, not a deploy.

Locked 2026-10-13: no Webflow; keep the Render path; pages stay in this folder; Key Ring Friends Pay now uses Stripe Checkout.

## What I actually hit

- Local shop: `http://127.0.0.1:8791/` - health `mode: demo`, catalog name MandMs3DPrints, 0 public products, Ask the bench present, no Discord on the page, From the printer present.
- Videos API: 19 clips, `live: true`, source is Desktop StarNet Trusted\\STARNET Storefront Website\\Embed Links to Videos from socials. Groups: Car Parts, Mechanical Things 2; For the House 5; Key Chain Animals 5 (includes 1 TikTok); One of a kind Lithophanes 4; Random Funzies 3.
- Wanted URL: `https://mandms3dprints.onrender.com/` - HTTP 404.
- Current public host: `https://forge-files.onrender.com/` - still Raz's Retro Resto with a Bench bag and Add to bag. Health: store "The Raz LAB", mode demo. Page has 0 MandMs3DPrints, 0 Ask the bench, 0 From the printer.
- GitHub `hewbrutis/forge-files` still has that older Raz shop (`index.html` title Raz's Retro Resto). `render.yaml` already names the service `mandms3dprints`.
- Render docs: a web service's `onrender.com` subdomain incorporates the Name field. https://render.com/docs/web-services

Pushing "this" means replacing that old Raz shop with the files in this `shop/` folder. A deploy of GitHub as it sits today would not ship MandMs3DPrints.

## Will it still work?

The page itself can run on Render. `server.py` binds `0.0.0.0` when the host sets `PORT`. Render web services are built for that. https://render.com/docs/web-services

Several pieces that work on this machine will not work the same way on the public host.

## Same on live

- The Raz LAB / by / MandMs3DPrints title stack, intro copy, empty best-work photo slots.
- From the printer carousels, as long as `videos.json` is in the deploy. Instagram iframes are `https://www.instagram.com/.../embed/` - they load from Instagram, not from this PC.
- Ask the bench bubble UI. Visitors can send. No Discord embed on the page.
- Hidden demo parts stay off the public catalog.
- Fake checkout stays off. Public host without a Stripe key is `catalog` mode; `POST /api/checkout` returns 503.

## Different on live

1. **It is not the site that is live today.** Live is still Raz's Retro Resto with a bag. MandMs3DPrints only exists on this machine until we push these files and Render is pointed at them.

2. **New Instagram or TikTok links will not auto-import on Render.** Local re-reads `C:\\Users\\Matt\\Desktop\\StarNet Trusted\\STARNET Storefront Website\\Embed Links to Videos from socials`. That folder is not on Render. Public `/api/videos` falls back to the `videos.json` snapshot (`live: false`). The StarNet routine "Import MandMs Instagram videos" hits this machine every 15 minutes. New desktop links need a refresh here, then a new deploy of `videos.json`.

3. **Ask the bench stores chat on the server disk.** Crew replies and Discord pings are localhost-only (`/api/bench/chats`, `/api/bench/chat`, `/api/bench/chat/pending`). Opening `/bench.html` on the public URL from your house is 403. The Discord ping routine talks to `127.0.0.1:8791`, not Render. Station Discord `1555588692943306802` stays notify-only and is still connected. Live visitor messages would sit in `chats.json` on the host until someone reads that file or we retarget the ping.

4. **Chat and stock files are ephemeral on Render Free.** Render spins a Free web service down after 15 minutes idle (~1 minute cold start) and wipes local files on restart/redeploy. Free services cannot attach a persistent disk. https://render.com/docs/free https://render.com/docs/disks

5. **The bench editor stays on this PC.** Inventory writes are 403 from the internet. Changing a part locally does not change the live catalog until `products.json` is pushed.

6. **Cards are on for Key Ring Friends.** Connect Stripe, then set `STRIPE_SECRET_KEY` on Render. Pay now creates a Checkout Session. Lithophanes and custom quotes still use Ask the bench.

7. **HTTPS vs this machine.** Local is http://127.0.0.1. Live is https. The page and chat token in the browser still work. Instagram may show its own login/cookie chrome to public visitors - that is Instagram, not our markup.

8. **The public name is still forge-files.** Until the Render service Name is `mandms3dprints`, the URL will not be `mandms3dprints.onrender.com`.
