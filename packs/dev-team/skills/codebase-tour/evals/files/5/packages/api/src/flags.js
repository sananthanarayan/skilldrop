// Feature flags come from a comma-separated env var, e.g. FEATURE_FLAGS=long-stays,new-pricing
const enabled = new Set(
  (process.env.FEATURE_FLAGS ?? '').split(',').map((f) => f.trim()).filter(Boolean),
);

export function isEnabled(flag) {
  return enabled.has(flag);
}
