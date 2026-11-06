const nodemailer = require('nodemailer');
const config = require('../config/default.json');

const transport = nodemailer.createTransport({
  host: config.smtp.host,
  port: config.smtp.port,
});

async function sendProcessingEmail(to, episodeTitle) {
  await transport.sendMail({
    from: config.smtp.from,
    to,
    subject: `"${episodeTitle}" is processing`,
    text: `We've received "${episodeTitle}" and started processing it. We'll publish it once the transcript is ready.`,
  });
}

module.exports = { sendProcessingEmail };
