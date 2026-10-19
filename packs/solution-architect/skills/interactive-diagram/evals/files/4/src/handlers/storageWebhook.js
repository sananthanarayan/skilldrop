const crypto = require('crypto');
const config = require('../../config/default.json');
const { query, mediaQueue } = require('../db');

function validSignature(rawBody, header) {
  if (!header) return false;
  const expected = crypto
    .createHmac('sha256', config.storage.webhookSecret)
    .update(rawBody)
    .digest('hex');
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(header));
}

async function handleStorageWebhook(req, res) {
  if (!validSignature(req.body, req.get('x-storage-signature'))) {
    return res.status(401).json({ error: 'bad signature' });
  }

  const event = JSON.parse(req.body.toString('utf8'));
  if (event.type !== 'object.finalized') {
    // Deletes, metadata updates etc. are acknowledged and ignored.
    return res.status(204).end();
  }

  const [episode] = await query(
    "UPDATE episodes SET status = 'uploaded', audio_url = $1 WHERE upload_key = $2 AND status = 'awaiting_upload' RETURNING id",
    [`${config.storage.publicBaseUrl}/${event.object.key}`, event.object.key]
  );
  if (!episode) {
    // Unknown key, or a retried webhook for an episode we already took.
    return res.status(200).json({ ignored: true });
  }

  await mediaQueue.add(
    'transcribe-episode',
    { episodeId: episode.id },
    { attempts: 3, backoff: { type: 'exponential', delay: 30000 } }
  );

  return res.status(202).json({ queued: episode.id });
}

module.exports = { handleStorageWebhook };
