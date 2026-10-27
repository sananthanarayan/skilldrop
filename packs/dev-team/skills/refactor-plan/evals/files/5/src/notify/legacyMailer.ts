// LegacyMailer — talks SMTP directly to the old relay.
// Written 2022. Do not add features here (says everyone, then adds features).

import nodemailer from "nodemailer";
import fs from "fs";
import path from "path";
import { logger } from "../lib/logger";
import { config } from "../lib/config";

export type TemplateName =
  | "order_shipped"
  | "order_confirmed"
  | "password_reset"
  | "welcome"
  | "weekly_digest";

export interface SendOptions {
  to: string | string[];
  template: TemplateName;
  vars: Record<string, unknown>;
  replyTo?: string;
  attachments?: { filename: string; content: Buffer }[];
  bccOps?: boolean;
}

const TEMPLATE_DIR = path.join(__dirname, "templates");
const templateCache: Record<string, string> = {};

let transport: nodemailer.Transporter | null = null;

function getTransport(): nodemailer.Transporter {
  if (!transport) {
    transport = nodemailer.createTransport({
      host: config.smtp.host,
      port: config.smtp.port,
      secure: false,
      auth: { user: config.smtp.user, pass: config.smtp.pass },
      pool: true,
      maxConnections: 3,
    });
  }
  return transport;
}

function loadTemplate(name: TemplateName): string {
  if (templateCache[name]) return templateCache[name];
  const file = path.join(TEMPLATE_DIR, `${name}.html`);
  const body = fs.readFileSync(file, "utf8");
  templateCache[name] = body;
  return body;
}

// Very small mustache-ish renderer. Unknown vars render as empty string.
export function render(tpl: string, vars: Record<string, unknown>): string {
  return tpl.replace(/\{\{\s*(\w+)\s*\}\}/g, (_m, key) => {
    const v = vars[key];
    if (v === undefined || v === null) return "";
    return String(v);
  });
}

function subjectFor(template: TemplateName, vars: Record<string, unknown>): string {
  switch (template) {
    case "order_shipped":
      return `Your order ${vars.orderNumber} is on its way`;
    case "order_confirmed":
      return `We've got your order ${vars.orderNumber}`;
    case "password_reset":
      return "Reset your password";
    case "welcome":
      return `Welcome, ${vars.firstName ?? "there"}!`;
    case "weekly_digest":
      return "Your week in review";
  }
}

function normaliseRecipients(to: string | string[]): string[] {
  const list = Array.isArray(to) ? to : to.split(",");
  return list
    .map((s) => s.trim().toLowerCase())
    .filter((s) => s.length > 0);
}

function isSuppressed(address: string): boolean {
  // suppression list is a flat file synced nightly from the old provider
  try {
    const raw = fs.readFileSync(config.smtp.suppressionFile, "utf8");
    return raw.split("\n").includes(address);
  } catch {
    return false;
  }
}

export class LegacyMailer {
  private sentCount = 0;

  async send(opts: SendOptions): Promise<boolean> {
    const recipients = normaliseRecipients(opts.to).filter((r) => !isSuppressed(r));
    if (recipients.length === 0) {
      logger.info("legacyMailer: all recipients suppressed", { template: opts.template });
      return true;
    }

    const html = render(loadTemplate(opts.template), opts.vars);
    const subject = subjectFor(opts.template, opts.vars);

    const message: nodemailer.SendMailOptions = {
      from: config.smtp.from,
      to: recipients.join(", "),
      subject,
      html,
      replyTo: opts.replyTo,
      attachments: opts.attachments,
    };
    if (opts.bccOps) {
      message.bcc = config.smtp.opsAddress;
    }

    try {
      await getTransport().sendMail(message);
      this.sentCount++;
      return true;
    } catch (err) {
      // TODO(2022): surface this properly. For now don't break checkout.
      logger.warn("legacyMailer: send failed", { err, template: opts.template });
      return true;
    }
  }

  async sendTemplate(template: TemplateName, to: string, vars: Record<string, unknown>) {
    return this.send({ template, to, vars });
  }

  async sendBulk(template: TemplateName, recipients: { to: string; vars: Record<string, unknown> }[]) {
    const results: boolean[] = [];
    for (const r of recipients) {
      // sequential on purpose: the relay rate-limits at ~5/s
      results.push(await this.send({ template, to: r.to, vars: r.vars }));
      await new Promise((res) => setTimeout(res, 200));
    }
    return results;
  }

  stats() {
    return { sent: this.sentCount };
  }
}

export const mailer = new LegacyMailer();
