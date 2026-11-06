const CSS = `
#parcelpost-chat { position: fixed; right: 24px; bottom: 24px; font: 14px/1.4 system-ui, sans-serif; }
#parcelpost-chat form { display: flex; gap: 8px; background: #fff; border-radius: 12px; padding: 12px; box-shadow: 0 4px 24px rgba(0,0,0,.15); }
#parcelpost-chat textarea { flex: 1; min-height: 40px; resize: none; border: 1px solid #d0d4dc; border-radius: 8px; padding: 8px; }
`;

export function injectStyles(root: HTMLElement) {
  const style = document.createElement('style');
  style.textContent = CSS;
  root.appendChild(style);
}
