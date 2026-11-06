const config = require('../../config/default.json');

async function submitTranscription(audioUrl, episodeId) {
  const response = await fetch(`${config.transcription.baseUrl}/v2/jobs`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${config.transcription.apiKey}`,
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      media_url: audioUrl,
      language: config.transcription.language,
      reference: String(episodeId),
      callback_url: `${config.publicUrl}/webhooks/transcription`,
    }),
  });

  if (!response.ok) {
    throw new Error(`transcription submit failed: ${response.status}`);
  }
  const body = await response.json();
  return body.job_id;
}

module.exports = { submitTranscription };
