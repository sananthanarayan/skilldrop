const ENDPOINT = 'https://chat.parcelpost.example/v1/messages';

export async function sendMessage(text: string) {
  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-widget-key': 'PLACEHOLDER_WIDGET_KEY' },
    body: JSON.stringify({ text, page: location.href }),
  });
  if (!res.ok) throw new Error(`send failed: ${res.status}`);
  return res.json();
}
