# MandMs3DPrints — local bench editor

Who: the Commander, restocking and rewriting printed parts.
One action: save a catalog change.

Open on this machine only: http://127.0.0.1:8791/bench.html

The public shop stays http://127.0.0.1:8791/ and reads the same `products.json`. Hide a part to pull it off the shop without deleting it.

Writes are refused unless the request comes from 127.0.0.1 / localhost. Public catalog mode still cannot checkout.

Shop chats land in the same bench page. Reply there so the visitor sees it in their bubble. Discord is notify-only — see shop/CHAT.md.
