import { useEffect, useRef } from 'react'
import Chart from 'chart.js/auto'
import type { ChartConfiguration } from 'chart.js'

export function QmChart({ config }: { config: ChartConfiguration }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    if (!canvas.current) return
    const chart = new Chart(canvas.current, config)
    return () => chart.destroy()
  }, [config])
  return <canvas ref={canvas} />
}
export { QmChart as Chart }
