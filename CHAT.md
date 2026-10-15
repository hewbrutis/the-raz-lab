# MandMs3DPrints — shop contact (Discord stays off the page)

Who: a visitor on the public shop who wants to ask Matt and Misti about a print.
One action: send a note from **Want what we got?** The shop emails `mandms3dprints@gmail.com`. StarNet is not required.

## Split (do not mix)
- Buyer UI: `shop/index.html` — **Want what we got?** opens a short email form. Name optional. Email required. After a successful send, the panel closes. It is not a live chat thread.
- Alert and reply: Gmail. Open `mandms3dprints@gmail.com`, hit Reply. That goes to the visitor's inbox. Gmail replies do **not** appear in the shop window.
- Do **not** put Discord on the shop page. Do **not** route this through the station Gmail tools.

## How it works without the station
1. Visitor sends from the form → `POST /api/chat` emails FormSubmit → `mandms3dprints@gmail.com`.
2. Reply-To on that mail is the visitor's address. Reply in Gmail. The conversation stays in email.
3. Two-way inbox-to-shop chat is not possible on this FormSubmit path. Do not keep the window open as if a reply will land there.

`GET /chats.json` is 404 on purpose. Tokens never go to Discord.

## First send
FormSubmit emails `mandms3dprints@gmail.com` a Confirm link the first time this shop address is used. Tap that once. After that, customer notes land in the inbox.

## Verify
- Public HTML has **Want what we got?**, an email field, **Send email**, and no chat log / message bubbles.
- After send, the panel closes. Zero `discord` strings on the public page.
