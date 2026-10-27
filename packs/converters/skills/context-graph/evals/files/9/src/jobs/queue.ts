import { Queue } from "bullmq";

const connection = { url: process.env.REDIS_URL };

export const emailQueue = new Queue("email", { connection });
export const orderExportQueue = new Queue("order-export", { connection });

export async function enqueueOrderConfirmation(orderId: string, to: string) {
  await emailQueue.add("order-confirmation", { orderId, to }, { attempts: 5 });
}
