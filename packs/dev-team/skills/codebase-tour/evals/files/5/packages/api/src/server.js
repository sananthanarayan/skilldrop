import express from 'express';
import { bookingsRouter } from './routes/bookings.js';

const app = express();
app.use(express.json());
app.use((req, _res, next) => {
  // Members are identified by the upstream proxy.
  const id = req.get('x-member-id');
  req.member = id ? { id } : null;
  next();
});
app.use(bookingsRouter);

const port = Number(process.env.PORT ?? 3000);
app.listen(port, () => console.log(`cabinbook api on :${port}`));
