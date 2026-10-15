# MandMs3DPrints — Key Ring Friends bag

Who: a visitor who wants to buy animal key chains from the Key Ring Friends row.
One action: pick 1, 5, or 10 of the same animal, then pay now on Stripe.

## Prices
- 1 of one animal: $4.99
- 5 of that same animal: $19.99
- 10 of that same animal: $37.99
- Not mix and match. No quantity 11. Different animals stay separate lines, each priced as its own 1 / 5 / 10 pack.

## Split
- Buyer UI: `shop/index.html` — pack buttons on each Key Ring Friend. Header **Bag** opens the cart. The bag popup has a required US shipping address form (street, city, state, ZIP). **Pay now** will not start without it, then creates a Stripe Checkout Session that also requires a US shipping address.
- Money: Stripe charges the card on that page. Balance hits the connected Stripe account immediately. Bank payout follows Stripe's normal schedule.
- Custom work still uses **Want what we got?** Lithophanes and example rows do not get pack buttons.

## Host
- Local review: `http://127.0.0.1:8791/`
- Planned public URL: `https://mandms3dprints.onrender.com/`
- Needs `STRIPE_SECRET_KEY` on the shop host. Connect Stripe in ABILITIES, then set that env var on Render.

## Verify
- Six Key Ring Friends, each with 1 / 5 / 10 pack buttons.
- 1 = $4.99. 5 = $19.99. 10 = $37.99.
- Two different animals in the bag stay two lines. Five of one plus one of another is $24.98, not a mixed group of 6.
- Pay now without a Stripe key returns 503 and does not email an unpaid order.
- Pay now with a Stripe key redirects to `checkout.stripe.com`.
- Pay now without street, city, state, or ZIP is refused. The old free-text “Where it ships” box is gone.
