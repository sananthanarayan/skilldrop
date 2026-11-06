const { Pool } = require('pg');
const IORedis = require('ioredis');
const { Queue } = require('bullmq');
const config = require('../config/default.json');

const pool = new Pool({ connectionString: config.databaseUrl });
const connection = new IORedis(config.redisUrl, { maxRetriesPerRequest: null });

const mediaQueue = new Queue('media', { connection });

async function query(text, params) {
  const result = await pool.query(text, params);
  return result.rows;
}

module.exports = { query, mediaQueue, connection };
