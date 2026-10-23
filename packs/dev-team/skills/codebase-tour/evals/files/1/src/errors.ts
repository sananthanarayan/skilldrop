export class HttpError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

export function badRequest(code: string, message: string): HttpError {
  return new HttpError(400, code, message);
}
