// Groups shipment rows by status for the Overview cards.
export function groupRows(rows) {
  return Object.groupBy(rows, (row) => row.status);
}
