import { Chart } from '@quillmark/ui'

const config = {
  type: 'line' as const,
  data: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], datasets: [{ label: 'Orders', data: [112, 98, 140, 131, 155] }] },
}

export default function Analytics() {
  return <Chart config={config} />
}
