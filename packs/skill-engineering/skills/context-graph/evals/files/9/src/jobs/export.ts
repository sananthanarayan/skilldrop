export async function exportOrder(data: { orderId: string }): Promise<void> {
  console.log(`would export order ${data.orderId} to the warehouse feed`);
}
