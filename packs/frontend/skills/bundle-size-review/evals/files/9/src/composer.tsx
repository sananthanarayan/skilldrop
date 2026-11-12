import { h } from 'preact';
import { useRef, useState } from 'preact/hooks';
import { sendMessage } from './api';
import { SHORTCODES } from './emoji/data';

// PR #412: turn :smile: style shortcodes into emoji as the visitor types.
const SHORTCODE_RE = /:([a-z0-9_+-]+):/g;
const expandShortcodes = (text: string) =>
  text.replace(SHORTCODE_RE, (m, code) => SHORTCODES[code] ?? m);

export function Composer({ openPicker }: { openPicker: (cb: (c: string) => void) => void }) {
  const [text, setText] = useState('');
  const input = useRef<HTMLTextAreaElement>(null);
  return (
    <form onSubmit={(e) => { e.preventDefault(); sendMessage(text); setText(''); }}>
      <textarea ref={input} value={text} onInput={(e) => setText(expandShortcodes(e.currentTarget.value))} />
      <button type="button" aria-label="Insert emoji" onClick={() => openPicker((c) => setText(text + c))}>☺</button>
      <button type="submit">Send</button>
    </form>
  );
}
