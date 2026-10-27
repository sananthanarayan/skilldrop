import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { CartItem, Address, ShippingOption } from "../types";

type Props = {
  items: CartItem[];
  onComplete: (orderId: string) => void;
};

export default function CheckoutPanel({ items, onComplete }: Props) {
  const [step, setStep] = useState<"address" | "shipping" | "payment">("address");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState<Address>({
    line1: "", line2: "", city: "", postcode: "", country: "GB",
  });
  const [addressErrors, setAddressErrors] = useState<Record<string, string>>({});
  const [shippingOptions, setShippingOptions] = useState<ShippingOption[]>([]);
  const [shipping, setShipping] = useState<ShippingOption | null>(null);
  const [promoCode, setPromoCode] = useState("");
  const [promoPercent, setPromoPercent] = useState(0);
  const [promoError, setPromoError] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [cardExpiry, setCardExpiry] = useState("");
  const [cardCvc, setCardCvc] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  // ---- totals (all money in pence) ----------------------------------
  const subtotal = items.reduce((sum, i) => sum + i.unitPence * i.qty, 0);
  const discount = Math.round(subtotal * (promoPercent / 100));
  const afterDiscount = subtotal - discount;
  const freeShipping = afterDiscount > 5000;
  const shippingPence = freeShipping ? 0 : shipping ? shipping.pence : 0;
  const total = afterDiscount + shippingPence;

  // ---- draft persistence ---------------------------------------------
  // keeps the form if the user navigates away
  useEffect(() => {
    localStorage.setItem(
      "checkout_draft",
      JSON.stringify({ email, address, promoCode, total })
    );
  }, [email, address, promoCode, total]);

  useEffect(() => {
    const raw = localStorage.getItem("checkout_draft");
    if (raw) {
      const d = JSON.parse(raw);
      setEmail(d.email || "");
      if (d.address) setAddress(d.address);
      if (d.promoCode) setPromoCode(d.promoCode);
    }
  }, []);

  // ---- address --------------------------------------------------------
  function validateAddress(): boolean {
    const errs: Record<string, string> = {};
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) errs.email = "Enter a valid email";
    if (!address.line1.trim()) errs.line1 = "Required";
    if (!address.city.trim()) errs.city = "Required";
    if (address.country === "GB" && !/^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$/i.test(address.postcode)) {
      errs.postcode = "Enter a valid UK postcode";
    }
    if (address.country !== "GB" && !address.postcode.trim()) errs.postcode = "Required";
    setAddressErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function goToShipping() {
    if (!validateAddress()) return;
    const res = await api.get(`/shipping/options?country=${address.country}&postcode=${address.postcode}`);
    setShippingOptions(res.data);
    setShipping(res.data[0] ?? null);
    setStep("shipping");
  }

  // ---- promo ----------------------------------------------------------
  async function applyPromo() {
    setPromoError("");
    if (!promoCode.trim()) return;
    try {
      const res = await api.get(`/promos/${encodeURIComponent(promoCode.trim().toUpperCase())}`);
      if (res.data.expired) {
        setPromoError("That code has expired");
        setPromoPercent(0);
      } else {
        setPromoPercent(res.data.percent);
      }
    } catch {
      setPromoError("Code not recognised");
      setPromoPercent(0);
    }
  }

  // ---- payment --------------------------------------------------------
  function validateCard(): string | null {
    const digits = cardNumber.replace(/\s/g, "");
    if (!/^\d{13,19}$/.test(digits)) return "Card number looks wrong";
    let sum = 0;
    for (let i = 0; i < digits.length; i++) {
      let d = parseInt(digits[digits.length - 1 - i], 10);
      if (i % 2 === 1) { d *= 2; if (d > 9) d -= 9; }
      sum += d;
    }
    if (sum % 10 !== 0) return "Card number looks wrong";
    if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(cardExpiry)) return "Expiry should be MM/YY";
    if (!/^\d{3,4}$/.test(cardCvc)) return "CVC should be 3 or 4 digits";
    return null;
  }

  async function submit() {
    const cardErr = validateCard();
    if (cardErr) { setSubmitError(cardErr); return; }
    setSubmitting(true);
    setSubmitError("");
    try {
      const tokenRes = await api.post("/payments/tokenise", {
        number: cardNumber.replace(/\s/g, ""), expiry: cardExpiry, cvc: cardCvc,
      });
      const orderRes = await api.post("/orders", {
        email, address, shippingId: shipping?.id, promoCode: promoPercent ? promoCode : null,
        items: items.map((i) => ({ sku: i.sku, qty: i.qty })),
        expectedTotalPence: total,
        paymentToken: tokenRes.data.token,
      });
      onComplete(orderRes.data.id);
    } catch (e: any) {
      setSubmitError(e?.response?.data?.message || "Payment failed, please try again");
    } finally {
      setSubmitting(false);
    }
  }

  const fmt = (p: number) => `£${(p / 100).toFixed(2)}`;

  // ---- render ---------------------------------------------------------
  return (
    <div className="checkout">
      <aside className="checkout__summary">
        {items.map((i) => (
          <div key={i.sku} className="row">
            <span>{i.name} x {i.qty}</span>
            <span>{fmt(i.unitPence * i.qty)}</span>
          </div>
        ))}
        {discount > 0 && <div className="row"><span>Discount</span><span>-{fmt(discount)}</span></div>}
        <div className="row"><span>Shipping</span><span>{freeShipping ? "Free" : fmt(shippingPence)}</span></div>
        <div className="row row--total"><span>Total</span><span>{fmt(total)}</span></div>
        <div className="promo">
          <input value={promoCode} onChange={(e) => setPromoCode(e.target.value)} placeholder="Promo code" />
          <button onClick={applyPromo}>Apply</button>
          {promoError && <p className="error">{promoError}</p>}
        </div>
      </aside>

      {step === "address" && (
        <section>
          <h2>Where should we send it?</h2>
          <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label>
          {addressErrors.email && <p className="error">{addressErrors.email}</p>}
          <label>Address line 1<input value={address.line1} onChange={(e) => setAddress({ ...address, line1: e.target.value })} /></label>
          {addressErrors.line1 && <p className="error">{addressErrors.line1}</p>}
          <label>Address line 2<input value={address.line2} onChange={(e) => setAddress({ ...address, line2: e.target.value })} /></label>
          <label>City<input value={address.city} onChange={(e) => setAddress({ ...address, city: e.target.value })} /></label>
          {addressErrors.city && <p className="error">{addressErrors.city}</p>}
          <label>Postcode<input value={address.postcode} onChange={(e) => setAddress({ ...address, postcode: e.target.value })} /></label>
          {addressErrors.postcode && <p className="error">{addressErrors.postcode}</p>}
          <label>Country
            <select value={address.country} onChange={(e) => setAddress({ ...address, country: e.target.value })}>
              <option value="GB">United Kingdom</option>
              <option value="IE">Ireland</option>
              <option value="FR">France</option>
              <option value="DE">Germany</option>
            </select>
          </label>
          <button onClick={goToShipping}>Continue to shipping</button>
        </section>
      )}

      {step === "shipping" && (
        <section>
          <h2>Delivery</h2>
          {shippingOptions.map((o) => (
            <label key={o.id} className="radio">
              <input type="radio" checked={shipping?.id === o.id} onChange={() => setShipping(o)} />
              {o.label} - {freeShipping ? "Free" : fmt(o.pence)}
            </label>
          ))}
          <button onClick={() => setStep("address")}>Back</button>
          <button onClick={() => setStep("payment")} disabled={!shipping}>Continue to payment</button>
        </section>
      )}

      {step === "payment" && (
        <section>
          <h2>Payment</h2>
          <label>Card number<input value={cardNumber} onChange={(e) => setCardNumber(e.target.value)} inputMode="numeric" /></label>
          <label>Expiry (MM/YY)<input value={cardExpiry} onChange={(e) => setCardExpiry(e.target.value)} /></label>
          <label>CVC<input value={cardCvc} onChange={(e) => setCardCvc(e.target.value)} inputMode="numeric" /></label>
          {submitError && <p className="error">{submitError}</p>}
          <button onClick={() => setStep("shipping")}>Back</button>
          <button onClick={submit} disabled={submitting}>{submitting ? "Paying..." : `Pay ${fmt(total)}`}</button>
        </section>
      )}
    </div>
  );
}
