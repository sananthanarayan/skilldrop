export interface Departure {
  route: string;
  minutes: number;
}

export function formatRow(d: Departure): string {
  return d.minutes <= 0 ? `${d.route}  due` : `${d.route}  ${d.minutes} min`;
}
