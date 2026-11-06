import { Router } from 'express';
import { validate } from '../middleware/validate.js';
import { createBooking } from '../services/bookings.js';

export const bookingsRouter = Router();

bookingsRouter.post('/bookings', validate('BookingRequest'), async (req, res, next) => {
  try {
    const booking = await createBooking(req.body, req.member);
    res.status(201).json(booking);
  } catch (err) {
    if (err.status) return res.status(err.status).json({ error: err.message });
    next(err);
  }
});
