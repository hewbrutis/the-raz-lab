import { json } from "../_lib.js";

const CLOSED = {
  ok: false,
  error: "Buying is closed on The Raz LAB. Message us if you want a print.",
};

export async function onRequestPost() {
  return json(CLOSED, 503);
}

export async function onRequestGet() {
  return json(CLOSED, 405);
}
