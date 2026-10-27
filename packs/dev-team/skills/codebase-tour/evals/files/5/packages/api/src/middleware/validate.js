import { schemas } from '../generated/schema.js';

export function validate(schemaName) {
  const schema = schemas[schemaName];
  return (req, res, next) => {
    const errors = [];
    for (const field of schema.required ?? []) {
      if (req.body?.[field] === undefined) errors.push(`${field} is required`);
    }
    for (const [field, rule] of Object.entries(schema.properties)) {
      const value = req.body?.[field];
      if (value === undefined) continue;
      if (rule.type === 'integer' && !Number.isInteger(value)) errors.push(`${field} must be an integer`);
      if (rule.minimum !== undefined && value < rule.minimum) errors.push(`${field} must be >= ${rule.minimum}`);
      if (rule.maximum !== undefined && value > rule.maximum) errors.push(`${field} must be <= ${rule.maximum}`);
    }
    if (errors.length) return res.status(400).json({ errors });
    next();
  };
}
