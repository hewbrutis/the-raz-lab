import {
  cleanEmail,
  cleanPlain,
  cleanShipTo,
  friendPrice,
  json,
  loadJsonAsset,
  MAX_NAME,
  moneyUsd,
} from "../_lib.js";

const STRIPE_CHECKOUT_URL = "https://api.stripe.com/v1/checkout/sessions";

function publicOrigin(request) {
  const url = new URL(request.url);
  return url.origin;
}

async function stripeCheckoutSession(env, packed, totalCents, email, name, shipTo, origin) {
  const secret = (env && (env.STRIPE_SECRET_KEY || env.STRIPE_API_KEY)) || "";
  if (!secret) {
    return { error: "Set STRIPE_SECRET_KEY on the Cloudflare Pages project, then redeploy." };
  }

  const fields = new URLSearchParams();
  fields.set("mode", "payment");
  fields.set("success_url", origin.replace(/\/$/, "") + "/?paid=1");
  fields.set("cancel_url", origin.replace(/\/$/, "") + "/#mm-bag");
  fields.set("customer_email", email);
  fields.set("billing_address_collection", "required");
  fields.append("shipping_address_collection[allowed_countries][]", "US");
  fields.set("payment_intent_data[description]", "Key Ring Friends — MandMs3DPrints");
  fields.set("payment_intent_data[metadata][shop]", "mandms3dprints");
  fields.set("payment_intent_data[metadata][name]", name.slice(0, 80));
  fields.set("payment_intent_data[metadata][ship_to]", shipTo.slice(0, 400));
  fields.set("metadata[shop]", "mandms3dprints");
  fields.set("metadata[name]", name.slice(0, 80));
  fields.set("metadata[email]", email.slice(0, 80));
  fields.set("metadata[ship_to]", shipTo.slice(0, 400));
  fields.set("metadata[total_cents]", String(totalCents));

  packed.forEach(function (row, i) {
    const prefix = "line_items[" + i + "]";
    fields.set(prefix + "[quantity]", "1");
    fields.set(prefix + "[price_data][currency]", "usd");
    fields.set(prefix + "[price_data][unit_amount]", String(row.cents));
    fields.set(prefix + "[price_data][product_data][name]", "Key Ring Friend — " + row.name);
    fields.set(prefix + "[price_data][product_data][description]", row.label + ". Same animal only.");
    fields.set(prefix + "[price_data][product_data][metadata][friend_id]", row.id);
    fields.set(prefix + "[price_data][product_data][metadata][qty]", String(row.qty));
  });

  const res = await fetch(STRIPE_CHECKOUT_URL, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + secret,
      "Content-Type": "application/x-www-form-urlencoded",
      "Idempotency-Key": "mm-bag-" + crypto.randomUUID().replace(/-/g, ""),
    },
    body: fields.toString(),
  });

  let data = {};
  try {
    data = await res.json();
  } catch (err) {
    return { error: "Stripe sent a bad reply." };
  }
  if (!res.ok) {
    const message =
      (data && data.error && data.error.message) ||
      ("Stripe said " + res.status + ".");
    return { error: message };
  }
  if (!data.url) {
    return { error: "Stripe did not return a checkout URL." };
  }
  return { session: data };
}

export async function onRequestPost(context) {
  let payload;
  try {
    payload = await context.request.json();
  } catch (err) {
    return json({ ok: false, error: "Bag is empty." }, 400);
  }

  let name;
  let email;
  let shipTo;
  try {
    name = cleanPlain(payload.name, "Name", MAX_NAME) || "Visitor";
    email = cleanEmail(payload.email);
    shipTo = cleanShipTo(payload.ship_to || payload.shipping);
  } catch (err) {
    return json({ ok: false, error: err.message || String(err) }, 400);
  }

  const itemsIn = payload.items;
  if (!Array.isArray(itemsIn) || !itemsIn.length) {
    return json({ ok: false, error: "Bag is empty." }, 400);
  }

  let friendsData;
  try {
    friendsData = await loadJsonAsset(context, "/friends.json");
  } catch (err) {
    return json({ ok: false, error: "Catalog is not on this host yet." }, 503);
  }
  const friends = {};
  (friendsData.items || []).forEach(function (row) {
    if (row && row.id) friends[row.id] = row;
  });

  const packed = [];
  let totalCents = 0;
  const seen = {};
  for (let i = 0; i < itemsIn.length; i++) {
    const row = itemsIn[i];
    if (!row || typeof row !== "object") {
      return json({ ok: false, error: "Bad bag line." }, 400);
    }
    const pid = String(row.id || "").trim();
    const qty = Number(row.qty || 0);
    const friend = friends[pid];
    const deal = friendPrice(qty);
    if (!friend || !deal || seen[pid]) {
      return json({
        ok: false,
        error: "Each Key Ring Friend is 1, 5, or 10 of that same animal. Not mix and match.",
      }, 400);
    }
    seen[pid] = true;
    packed.push({
      id: pid,
      name: friend.name || pid,
      qty: qty,
      cents: deal.total_cents,
      label: deal.label,
    });
    totalCents += deal.total_cents;
  }

  const origin = publicOrigin(context.request);
  const result = await stripeCheckoutSession(
    context.env,
    packed,
    totalCents,
    email,
    name,
    shipTo,
    origin
  );
  if (result.error || !result.session) {
    return json({
      ok: false,
      error: result.error || "Could not start Stripe checkout.",
    }, 503);
  }
  return json({
    ok: true,
    checkout_url: result.session.url,
    session_id: result.session.id,
    count: packed.reduce(function (sum, row) { return sum + row.qty; }, 0),
    total: moneyUsd(totalCents),
    items: packed,
  });
}

export async function onRequestGet() {
  return json({ ok: false, error: "POST a bag to pay." }, 405);
}
