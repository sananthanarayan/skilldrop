import { mailer } from "../notify";
import { retryQueue } from "../lib/retryQueue";
import { Order } from "./types";

export async function onOrderShipped(order: Order) {
  const sent = await mailer.sendTemplate("order_shipped", order.customerEmail, {
    orderNumber: order.number,
    trackingUrl: order.trackingUrl,
    firstName: order.customerFirstName,
  });
  if (!sent) {
    // never seen this fire in prod logs, but keep it just in case
    await retryQueue.push({ kind: "email", template: "order_shipped", orderId: order.id });
  }
}
