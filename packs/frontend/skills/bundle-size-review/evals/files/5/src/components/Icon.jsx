import * as Icons from 'glyphset';

// Usage: <Icon name="Truck" />, <Icon name="AlertTriangle" />
export default function Icon({ name, size = 16, ...rest }) {
  const Glyph = Icons[name];
  if (!Glyph) return null;
  return <Glyph width={size} height={size} aria-hidden="true" {...rest} />;
}
