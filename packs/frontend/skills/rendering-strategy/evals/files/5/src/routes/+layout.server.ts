import type { LayoutServerLoad } from './$types';

// root layout: every page gets the user so the nav can show "Log in" or "Open dashboard"
export const load: LayoutServerLoad = async ({ locals }) => {
  return {
    user: locals.user
      ? { name: locals.user.name, org: locals.user.orgName, plan: locals.user.plan }
      : null
  };
};
