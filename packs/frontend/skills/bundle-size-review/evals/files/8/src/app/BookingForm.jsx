import { useMemo, useState } from 'react';
import { DatePicker } from '@northwind/datepicker';
import { format, parseISO } from 'date-fns';
import { debounce } from '../utils/format';

export default function BookingForm() {
  const [departure, setDeparture] = useState('2027-06-14');
  const [query, setQuery] = useState('');
  const search = useMemo(() => debounce((q) => fetch(`/api/cabins?q=${encodeURIComponent(q)}`), 300), []);

  return (
    <form>
      <DatePicker value={parseISO(departure)} onChange={(d) => setDeparture(format(d, 'yyyy-MM-dd'))} />
      <p>Departing {format(parseISO(departure), 'EEEE d MMMM yyyy')}</p>
      <input value={query} onChange={(e) => { setQuery(e.target.value); search(e.target.value); }} />
    </form>
  );
}
