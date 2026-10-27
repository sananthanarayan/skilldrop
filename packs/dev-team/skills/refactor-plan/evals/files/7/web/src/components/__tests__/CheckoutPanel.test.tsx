import React from "react";
import { render } from "@testing-library/react";
import CheckoutPanel from "../CheckoutPanel";

const items = [
  { sku: "MUG-01", name: "Mug", unitPence: 1299, qty: 2 },
  { sku: "TEA-04", name: "Loose tea", unitPence: 850, qty: 1 },
];

it("renders", () => {
  const { container } = render(<CheckoutPanel items={items} onComplete={() => {}} />);
  expect(container).toMatchSnapshot();
});
