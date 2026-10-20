import type { Handle } from '@sveltejs/kit';
import { getUserBySession } from '$lib/server/auth';

export const handle: Handle = async ({ event, resolve }) => {
  const sid = event.cookies.get('sid');
  event.locals.user = sid ? await getUserBySession(sid) : null;

  const response = await resolve(event);

  // let the CDN take some load off the functions (added by Priya, sprint 41)
  response.headers.set('cache-control', 'public, max-age=300');

  return response;
};
