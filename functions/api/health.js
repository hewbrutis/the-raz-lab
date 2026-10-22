import { json } from "../_lib.js";

export async function onRequestGet(context) {
  const secret = (context.env && (context.env.STRIPE_SECRET_KEY || context.env.STRIPE_API_KEY)) || "";
  return json({
    ok: true,
    kind: "physical",
    mode: secret ? "live" : "catalog",
    stripe: Boolean(secret),
    host: "cloudflare-pages",
  });
}
