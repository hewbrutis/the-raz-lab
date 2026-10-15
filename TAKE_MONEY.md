# After Stripe is connected — order of operations

Who: a customer buying Key Ring Friends from MandMs3DPrints / The Raz LAB.
One action: pay for 1, 5, or 10 of the same animal.

Stripe connected in ABILITIES is not enough by itself. The shop host still needs `STRIPE_SECRET_KEY` (or `STRIPE_API_KEY`), and a real customer needs a public https shop URL. Local `http://127.0.0.1:8791/` cannot take money from someone off this PC.

## Before a customer can pay

1. Connect Stripe (ABILITIES › DISCOVER › CATALOG — Stripe).
2. Put the secret key on the shop host as `STRIPE_SECRET_KEY`.
3. Confirm `/api/health` returns `"stripe": true` and `"mode": "live"`.
4. Put the shop on a public https URL (planned: `https://mandms3dprints.onrender.com/`).
5. In the Stripe Dashboard, add the bank account that should receive payouts.

## What the customer does

1. Pick **1**, **5**, or **10** of one Key Ring Friend. Not mix and match. Different animals stay separate lines, each its own 1 / 5 / 10 pack.
2. Bag opens. They enter email and a US shipping address: street, city, state, ZIP. Name is optional. Apt is optional.
3. They click **Pay now**. The shop will not open Stripe without that address.

Prices the shop will send to Stripe:
- 1 = $4.99
- 5 = $19.99
- 10 = $37.99

## What the shop does (no card on our page)

4. Browser `POST /api/bag` with name, email, structured shipping, and the pack lines.
5. Server refuses empty bags, qty that is not 1 / 5 / 10, two lines of the same animal, and a missing or incomplete shipping address.
6. Server creates a Stripe Checkout Session (`mode=payment`) with those line items, their email, ship-to in metadata, and `shipping_address_collection` required for the US. Stripe Checkout also asks for the shipping address.
7. Server returns `checkout_url`.
8. Browser sends them to Stripe-hosted Checkout (`checkout.stripe.com`).

We never see the card. Stripe collects it.

## When money actually moves

9. They pay on Stripe. **That is when the card is charged.**
10. Stripe redirects them back to the shop at `/?paid=1`.
11. The bag clears and the page says: “Paid. Stripe has the money. We print and ship next.”
12. Balance hits the connected Stripe account right then.
13. Bank payout is later, on Stripe’s schedule — first live payout is typically 7–14 days, then the account’s normal payout cadence. https://docs.stripe.com/payouts

If they cancel, Stripe sends them back to `/#mm-bag`. Nothing is charged.

## After they pay — your job

14. Check the Stripe Dashboard (Payments) for the paid Checkout Session. Name, email, and ship-to are in metadata.
15. Print that pack and ship it.

The success page is a thank-you, not proof you can skip the Dashboard. Stripe says a buyer can pay and never land on `/?paid=1` (closed tab, dropped connection). This shop does not yet listen for `checkout.session.completed`. Until that webhook exists, treat Dashboard (or Stripe’s payment email) as the source of truth for “print this.”

## What this path is not

- **Want what we got?** is email to `mandms3dprints@gmail.com`. It does not take money.
- Connecting the Stripe *query* connector in StarNet does not charge cards. The shop charges with `STRIPE_SECRET_KEY` on the host.
- Coloring-book / MandMs2DPrints pages stay parked. This sequence is 3D shop only.

Sources: `shop/index.html` (Pay now → `/api/bag` → `checkout_url`), `shop/server.py` (`_handle_bag_post`, `stripe_checkout_session`), https://docs.stripe.com/payments/checkout/how-checkout-works, https://docs.stripe.com/payments/checkout/fulfillment, https://docs.stripe.com/payouts
