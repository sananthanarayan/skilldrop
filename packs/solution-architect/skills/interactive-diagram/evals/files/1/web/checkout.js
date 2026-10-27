export async function placeOrder(cart, email, shopId) {
  const res = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items: cart.items, email, shop_id: shopId }),
  });
  if (!res.ok) throw new Error((await res.json()).error);
  return (await res.json()).id;
}
