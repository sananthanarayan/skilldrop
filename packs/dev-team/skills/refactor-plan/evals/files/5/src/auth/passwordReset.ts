import { mailer } from "../notify";
import { users } from "../lib/users";
import { tokens } from "../lib/tokens";

export async function requestPasswordReset(email: string) {
  const user = await users.findByEmail(email);
  // Always respond the same way whether or not the user exists.
  if (!user) return { ok: true };
  const token = await tokens.issueReset(user.id);
  await mailer.send({
    to: user.email,
    template: "password_reset",
    vars: { resetUrl: `https://app.example.test/reset?t=${token}` },
  });
  return { ok: true };
}
