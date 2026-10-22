import { json, loadJsonAsset } from "../_lib.js";

export async function onRequestGet(context) {
  try {
    const data = await loadJsonAsset(context, "/videos.json");
    return json(data);
  } catch (err) {
    return json({ ok: false, error: "Videos are not on this host yet." }, 404);
  }
}
