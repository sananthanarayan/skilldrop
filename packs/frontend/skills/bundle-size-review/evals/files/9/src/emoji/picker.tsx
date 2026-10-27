import { h, render } from 'preact';
import { useState } from 'preact/hooks';
import { EMOJI, type Emoji } from './data';

function Picker({ onPick }: { onPick: (c: string) => void }) {
  const [q, setQ] = useState('');
  const shown = (EMOJI as Emoji[]).filter((e) => !q || e.keywords.some((k) => k.includes(q))).slice(0, 200);
  return (
    <div class="pp-picker">
      <input placeholder="Search emoji" value={q} onInput={(e) => setQ(e.currentTarget.value)} />
      <div class="pp-grid">
        {shown.map((e) => <button key={e.shortcode} title={e.name} onClick={() => onPick(e.char)}>{e.char}</button>)}
      </div>
    </div>
  );
}

export default function mountPicker(root: HTMLElement, onPick: (c: string) => void) {
  const el = document.createElement('div');
  root.appendChild(el);
  render(<Picker onPick={onPick} />, el);
}
