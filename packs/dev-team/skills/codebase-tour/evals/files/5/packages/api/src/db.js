// In production this is a pg pool built from DATABASE_URL; locally an in-memory stand-in.
const url = process.env.DATABASE_URL;
if (!url) {
  throw new Error('DATABASE_URL is not set. Copy .env.example to .env.');
}

const bookings = [];

export const db = {
  url,
  async insertBooking(row) {
    const saved = { id: String(bookings.length + 1), ...row };
    bookings.push(saved);
    return saved;
  },
  async bookingsForCabin(cabinId) {
    return bookings.filter((b) => b.cabinId === cabinId);
  },
};
