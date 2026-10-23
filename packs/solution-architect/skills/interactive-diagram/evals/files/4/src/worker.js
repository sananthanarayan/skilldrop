const { Worker } = require('bullmq');
const config = require('../config/default.json');
const { query, mediaQueue, connection } = require('./db');
const { transcribeEpisode } = require('./jobs/transcribeEpisode');

async function reindexSearch() {
  const rows = await query(
    "SELECT id, title, transcript FROM episodes WHERE status = 'published' AND updated_at > now() - interval '1 day'"
  );
  if (rows.length === 0) return;
  await fetch(`${config.search.url}/indexes/${config.search.index}/documents`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(rows),
  });
}

const handlers = {
  'transcribe-episode': transcribeEpisode,
  'nightly-reindex': reindexSearch,
};

const worker = new Worker('media', (job) => handlers[job.name](job), { connection });

worker.on('failed', async (job, err) => {
  console.error(`job ${job.name} ${job.id} failed: ${err.message}`);
  if (job.name === 'transcribe-episode' && job.attemptsMade >= job.opts.attempts) {
    await query("UPDATE episodes SET status = 'failed' WHERE id = $1", [job.data.episodeId]);
  }
});

mediaQueue.add('nightly-reindex', {}, { repeat: { pattern: '0 3 * * *' } });
