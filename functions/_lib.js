/** Shared Raz LAB shop helpers for Cloudflare Pages Functions. */
export const FRIEND_PRICE_SINGLE = 499;
export const FRIEND_PRICE_FIVE = 1999;
export const FRIEND_PRICE_TEN = 3799;

export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export const MAX_SHIP_TO = 400;
export const MAX_NAME = 80;
export const MAX_EMAIL = 80;

export function json(data, status) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

export function moneyUsd(cents) {
  return "$" + (Number(cents) / 100).toFixed(2);
}

export function packCents(qty) {
  qty = Number(qty);
  if (qty === 1) return FRIEND_PRICE_SINGLE;
  if (qty === 5) return FRIEND_PRICE_FIVE;
  if (qty === 10) return FRIEND_PRICE_TEN;
  return null;
}

export function friendPrice(qty) {
  const cents = packCents(qty);
  if (cents == null) return null;
  qty = Number(qty);
  return {
    qty: qty,
    count: qty,
    total_cents: cents,
    label: qty + " for " + moneyUsd(cents),
  };
}

export function friendPriceTable() {
  const packs = [1, 5, 10].map(function (qty) {
    const cents = packCents(qty);
    return {
      qty: qty,
      cents: cents,
      money: moneyUsd(cents),
      label: qty + " for " + moneyUsd(cents),
    };
  });
  return {
    single_cents: FRIEND_PRICE_SINGLE,
    five_cents: FRIEND_PRICE_FIVE,
    ten_cents: FRIEND_PRICE_TEN,
    single: moneyUsd(FRIEND_PRICE_SINGLE),
    five: moneyUsd(FRIEND_PRICE_FIVE),
    ten: moneyUsd(FRIEND_PRICE_TEN),
    line: packs.map(function (p) { return p.label; }).join(" · "),
    packs: packs,
  };
}

export function cleanPlain(raw, field, maximum) {
  let text = String(raw == null ? "" : raw).trim();
  let cleaned = "";
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === "\n" || ch === "\r" || ch === "\t") cleaned += " ";
    else if (ch.charCodeAt(0) >= 32) cleaned += ch;
  }
  text = cleaned.replace(/ +/g, " ").trim();
  if (text.length > maximum) {
    throw new Error(field + " is too long.");
  }
  return text;
}

export function cleanEmail(raw) {
  const email = cleanPlain(raw, "Email", MAX_EMAIL);
  if (!email) throw new Error("Email is required so we can reply.");
  if (!EMAIL_RE.test(email)) throw new Error("That email does not look right.");
  return email;
}

export function cleanShipTo(raw) {
  if (raw && typeof raw === "object") {
    const parts = [
      raw.line1 || raw.street || "",
      raw.line2 || raw.apt || "",
      raw.city || "",
      raw.state || "",
      raw.postal_code || raw.zip || "",
    ];
    raw = parts.map(function (part) { return String(part).trim(); }).filter(Boolean).join(", ");
  }
  let text = String(raw == null ? "" : raw).trim();
  let cleaned = "";
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === "\r" || ch === "\t") cleaned += " ";
    else if (ch === "\n") cleaned += "\n";
    else if (ch.charCodeAt(0) >= 32) cleaned += ch;
  }
  text = cleaned.replace(/[ ]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
  if (!text) throw new Error("Where it ships is required.");
  if (text.length > MAX_SHIP_TO) throw new Error("Where it ships is too long.");
  return text;
}

export async function loadJsonAsset(context, pathname) {
  const url = new URL(pathname, context.request.url);
  const res = await fetch(url, { method: "GET" });
  if (!res.ok) {
    throw new Error("Could not read " + pathname);
  }
  return res.json();
}
