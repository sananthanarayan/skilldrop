import React from "react";
import { CartItem } from "../types";

type Props = {
  items: CartItem[];
  promoPercent: number;
  shippingPence: number;
};

// header dropdown cart; same maths as CheckoutPanel
export default function MiniCart({ items, promoPercent, shippingPence }: Props) {
  const afterDiscount = items.reduce(
    (sum, i) => sum + Math.round(i.unitPence * i.qty * (1 - promoPercent / 100)),
    0
  );
  const discount = items.reduce((s, i) => s + i.unitPence * i.qty, 0) - afterDiscount;
  const freeShipping = afterDiscount >= 5000;
  const total = afterDiscount + (freeShipping ? 0 : shippingPence);
  const fmt = (p: number) => `£${(p / 100).toFixed(2)}`;

  return (
    <div className="minicart">
      {items.map((i) => (
        <div key={i.sku} className="minicart__row">
          {i.name} x {i.qty} <span>{fmt(i.unitPence * i.qty)}</span>
        </div>
      ))}
      {discount > 0 && <div className="minicart__row">Discount -{fmt(discount)}</div>}
      <div className="minicart__total">Total {fmt(total)}</div>
      {freeShipping && <p className="minicart__hint">You've got free delivery</p>}
    </div>
  );
}
