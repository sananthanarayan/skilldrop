export const idempotencyStore = {
  async get(_key: string): Promise<any> { return undefined; },
  async put(_key: string, _value: unknown, _ttlSeconds: number): Promise<void> {},
};
