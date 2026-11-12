export async function sendEmail(data: { orderId: string; to: string }): Promise<void> {
  console.log(`would send order confirmation for ${data.orderId} to ${data.to}`);
}
