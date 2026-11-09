import { json } from "../_lib.js";

export async function onRequestGet() {
  return json({ ok: false, error: "POST a note to send it." }, 405);
}

export async function onRequestPost() {
  return json({
    ok: false,
    error: "Use the shop form. This route does not send mail.",
  }, 410);
}
