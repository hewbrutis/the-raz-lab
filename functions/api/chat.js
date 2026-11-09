import { json, cleanPlain, cleanEmail } from "../_lib.js";

const CHAT_TO = "mandms3dprints@gmail.com";
const FORMSUBMIT_URL = "https://formsubmit.co/ajax/" + CHAT_TO;
const MAX_CHAT_TEXT = 800;
const MAX_CHAT_NAME = 40;

function cleanChatText(raw) {
  const text = cleanPlain(raw, "Message", MAX_CHAT_TEXT);
  if (!text) throw new Error("Message is required.");
  return text;
}

function mailBody(name, email, text) {
  return (
    "Want what we got? from the MandMs3DPrints shop.\n\n" +
    "Name: " + name + "\n" +
    "Reply to: " + email + "\n\n" +
    text + "\n"
  );
}

export async function onRequestGet() {
  return json({ ok: false, error: "POST a note to send it." }, 405);
}

export async function onRequestPost(context) {
  let payload;
  try {
    payload = await context.request.json();
  } catch (err) {
    return json({ ok: false, error: "Bad JSON." }, 400);
  }

  let name;
  let email;
  let text;
  try {
    text = cleanChatText(payload && payload.text);
    name = cleanPlain(payload && payload.name, "Name", MAX_CHAT_NAME) || "Visitor";
    email = cleanEmail(payload && payload.email);
  } catch (err) {
    return json({ ok: false, error: err.message || "Could not read that note." }, 400);
  }

  const origin = context.request.headers.get("Origin") || "https://therazlab.com";
  const referer = context.request.headers.get("Referer") || "https://therazlab.com/";
  const body = new URLSearchParams({
    name: name,
    email: email,
    _replyto: email,
    _subject: "Want what we got? from " + name,
    message: mailBody(name, email, text),
    _template: "box",
    _captcha: "false",
  });

  const ac = new AbortController();
  const timer = setTimeout(function () { ac.abort(); }, 8000);
  let res;
  let raw = "";
  try {
    res = await fetch(FORMSUBMIT_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json",
        "User-Agent": "Mozilla/5.0 MandMs3DPrints-shop/1.0",
        Referer: referer,
        Origin: origin,
      },
      body: body.toString(),
      signal: ac.signal,
    });
    raw = await res.text();
  } catch (err) {
    return json({
      ok: false,
      error: "Could not reach the mail host. Instagram is @mandms3dprints if this box dies.",
    }, 502);
  } finally {
    clearTimeout(timer);
  }

  let data = {};
  try {
    data = JSON.parse(raw || "{}");
  } catch (err) {
    data = {};
  }

  const success = String((data && data.success) || "").toLowerCase();
  const message = String((data && data.message) || "");
  if (success === "true" || success === "1") {
    return json({ ok: true, mailed: "sent" });
  }
  if (/confirm|activation/i.test(message) || /confirm|activation/i.test(raw)) {
    return json({ ok: true, mailed: "confirm" });
  }
  if (res && (res.status === 200 || res.status === 201 || res.status === 202) && !message) {
    return json({ ok: true, mailed: "sent" });
  }

  return json({
    ok: false,
    error: message || "Could not email the bench. Instagram is @mandms3dprints if this box dies.",
  }, 502);
}
