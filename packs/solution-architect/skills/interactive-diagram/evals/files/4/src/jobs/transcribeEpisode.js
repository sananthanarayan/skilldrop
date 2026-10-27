const { query } = require('../db');
const { submitTranscription } = require('../clients/transcription');
const { sendProcessingEmail } = require('../mailer');

async function transcribeEpisode(job) {
  const [episode] = await query(
    `SELECT e.id, e.title, e.audio_url, c.email, c.notify_on_processing
       FROM episodes e
       JOIN shows s ON s.id = e.show_id
       JOIN creators c ON c.id = s.creator_id
      WHERE e.id = $1`,
    [job.data.episodeId]
  );
  if (!episode) return;

  const transcriptionJobId = await submitTranscription(episode.audio_url, episode.id);

  await query(
    "UPDATE episodes SET status = 'transcribing', transcription_job_id = $1 WHERE id = $2",
    [transcriptionJobId, episode.id]
  );

  if (episode.notify_on_processing) {
    await sendProcessingEmail(episode.email, episode.title);
  }
}

module.exports = { transcribeEpisode };
