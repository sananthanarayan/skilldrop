import { Worker } from "bullmq";
import { sendEmail } from "./email";
import { exportOrder } from "./export";

const connection = { url: process.env.REDIS_URL };

new Worker("email", async (job) => sendEmail(job.data), { connection });
new Worker("order-export", async (job) => exportOrder(job.data), { connection });
