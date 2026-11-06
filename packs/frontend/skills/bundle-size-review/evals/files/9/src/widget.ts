import { render, h } from 'preact';
import { Composer } from './composer';
import { injectStyles } from './styles';

const root = document.createElement('div');
root.id = 'parcelpost-chat';
document.body.appendChild(root);
injectStyles(root);

async function openPicker(onPick: (char: string) => void) {
  const { default: mountPicker } = await import('./emoji/picker');
  mountPicker(root, onPick);
}

render(h(Composer, { openPicker }), root);
