# castbox-media

Backend for the Hollowbrook Podcast Network's hosting platform.

## What it does

When a creator finishes uploading an episode, the object store sends us a
webhook. We then transcode and transcribe the audio, index the transcript in
search so listeners can find episodes by what was said, and purge the CDN so
the new episode shows up in the RSS feed straight away. The creator gets an
email when processing starts.

## Stack

- Node 20, Express (API) and BullMQ (background jobs)
- PostgreSQL (`episodes`, `shows`, `creators`)
- Redis (job queue)
- Transcription vendor HTTP API (api.transcribe.example.test)
- Search service (search.internal.test)
- CDN in front of the RSS feeds (cdn.example.test)
- SMTP relay for creator emails

## Running

    npm run api      # node src/server.js
    npm run worker   # node src/worker.js
