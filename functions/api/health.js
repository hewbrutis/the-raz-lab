import { json } from "../_lib.js";

export async function onRequestGet() {
  return json({
    ok: true,
    kind: "physical",
    mode: "catalog",
    stripe: false,
    host: "cloudflare-pages",
    buying: false,
  });
}
