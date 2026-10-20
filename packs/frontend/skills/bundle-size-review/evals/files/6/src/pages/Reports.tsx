import { useEffect, useRef } from 'react'
import * as echarts from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useLocale } from '../i18n/useLocale'

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

export default function Reports() {
  const el = useRef<HTMLDivElement>(null)
  const lang = useLocale()

  useEffect(() => {
    if (!el.current) return
    const chart = echarts.init(el.current, undefined, { locale: lang === 'de' ? 'DE' : 'EN' })
    chart.setOption({
      tooltip: {},
      legend: {},
      xAxis: { type: 'category', data: ['B1', 'B2', 'B3', 'B4'] },
      yAxis: { type: 'value' },
      series: [
        { type: 'bar', name: 'TEU', data: [420, 380, 515, 290] },
        { type: 'line', name: 'Target', data: [400, 400, 400, 400] },
      ],
    })
    return () => chart.dispose()
  }, [lang])

  return <div ref={el} style={{ height: 360 }} />
}
