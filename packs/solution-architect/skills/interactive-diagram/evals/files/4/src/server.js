const express = require('express');
const config = require('../config/default.json');
const { query } = require('./db');
const { handleStorageWebhook } = require('./handlers/storageWebhook');

const app = express();

// Raw body is needed so the storage webhook signature can be checked.
app.post('/webhooks/storage', express.raw({ type: 'application/json' }), handleStorageWebhook);

app.use(express.json());

app.get('/feeds/:showId.xml', async (req, res) => {
  const [show] = await query('SELECT id, title, description FROM shows WHERE id = $1', [req.params.showId]);
  if (!show) return res.status(404).end();
  const episodes = await query(
    "SELECT title, audio_url, published_at FROM episodes WHERE show_id = $1 AND status = 'published' ORDER BY published_at DESC",
    [show.id]
  );
  res.type('application/rss+xml').send(renderRss(show, episodes));
});

app.get('/healthz', (req, res) => res.send('ok'));

function renderRss(show, episodes) {
  const items = episodes
    .map((e) => `<item><title>${e.title}</title><enclosure url="${e.audio_url}" type="audio/mpeg"/></item>`)
    .join('');
  return `<?xml version="1.0"?><rss version="2.0"><channel><title>${show.title}</title>${items}</channel></rss>`;
}

app.listen(config.port, () => console.log(`api listening on ${config.port}`));
