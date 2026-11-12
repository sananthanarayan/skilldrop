import type { PageServerLoad } from './$types';
import { priceTable } from '$lib/pricing';

const CURRENCY: Record<string, 'USD' | 'EUR' | 'GBP'> = { GB: 'GBP', DE: 'EUR', FR: 'EUR', NL: 'EUR' };

export const load: PageServerLoad = async ({ request }) => {
  const country = request.headers.get('x-country') ?? 'US';
  const currency = CURRENCY[country] ?? 'USD';
  return { currency, plans: priceTable(currency) };
};
