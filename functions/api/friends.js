import { friendPriceTable, json, loadJsonAsset } from "../_lib.js";

export async function onRequestGet(context) {
  let data;
  try {
    data = await loadJsonAsset(context, "/friends.json");
  } catch (err) {
    return json({
      title: "Key Ring Friends",
      lede: "",
      price: friendPriceTable(),
      items: [],
    });
  }
  const items = Array.isArray(data && data.items) ? data.items : [];
  return json({
    title: (data && data.title) || "Key Ring Friends",
    lede: (data && data.lede) || "",
    price: friendPriceTable(),
    items: items,
  });
}
