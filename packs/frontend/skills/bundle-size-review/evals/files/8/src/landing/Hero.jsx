import { useState } from 'react';
import { titleCase } from '../utils/format';

export default function Hero() {
  const [email, setEmail] = useState('');
  const headline = titleCase('SAIL THE NORTHERN FJORDS THIS SUMMER');
  return (
    <section className="hero">
      <h1>{headline}</h1>
      <p>Small-ship cruises from Bergen and Tromsø, May to September.</p>
      <form action="/api/waitlist" method="post">
        <input type="email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button type="submit">Join the waitlist</button>
      </form>
    </section>
  );
}
