import OpenAI from "openai";
const client = new OpenAI();
// Sends the user's journal entry to the model to suggest the next habit.
export async function suggest(entry: string) {
  return client.chat.completions.create({ model: "gpt-4.1-mini", messages: [{ role: "user", content: entry }] });
}
