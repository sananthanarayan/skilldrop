// Nightly weekly-digest sender. Runs from the ops cron box, not the app.
// Copied the SMTP bits out of legacyMailer so this could run without
// building the TS app (2023).

const nodemailer = require("nodemailer");
const fs = require("fs");
const { getDigestRecipients } = require("../dist/lib/digest");

const transport = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: Number(process.env.SMTP_PORT || 25),
  auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
});

function render(tpl, vars) {
  return tpl.replace(/\{\{\s*(\w+)\s*\}\}/g, (_m, k) => (vars[k] == null ? "" : String(vars[k])));
}

async function main() {
  const tpl = fs.readFileSync(__dirname + "/../src/notify/templates/weekly_digest.html", "utf8");
  const recipients = await getDigestRecipients();
  for (const r of recipients) {
    // no suppression-list check here
    await transport.sendMail({
      from: process.env.SMTP_FROM,
      to: r.email,
      subject: "Your week in review",
      html: render(tpl, r.vars),
    });
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
