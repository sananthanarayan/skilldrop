import React from "react";
import { useNavigate } from "react-router-dom";

// Shown when a returning visitor lands on /checkout/review from the
// "you left something behind" email.
export default function OrderReview() {
  const navigate = useNavigate();
  const raw = localStorage.getItem("checkout_draft");
  const draft = raw ? JSON.parse(raw) : null;

  if (!draft || !draft.email) {
    navigate("/cart");
    return null;
  }

  return (
    <main className="review">
      <h1>Pick up where you left off</h1>
      <p>We saved your details for {draft.email}.</p>
      <p>Your total was <strong>£{(draft.total / 100).toFixed(2)}</strong>.</p>
      <button onClick={() => navigate("/checkout")}>Continue to checkout</button>
    </main>
  );
}
