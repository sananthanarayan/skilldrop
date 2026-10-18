# Gilded Lantern Box Office

Online ticketing for the Gilded Lantern Theatre.

## Architecture
- Django web app behind nginx
- Postgres database
- Redis for sessions
- RabbitMQ for the background job queue (ticket PDFs and confirmation emails)
- Admin console at /admin (separate service)
- Nightly sales reports
