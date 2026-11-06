import EMOJI from './emoji-data.json';

export interface Emoji { char: string; shortcode: string; name: string; group: string; keywords: string[] }

export { EMOJI };
export const SHORTCODES: Record<string, string> = Object.fromEntries(
  (EMOJI as Emoji[]).map((e) => [e.shortcode, e.char]),
);
