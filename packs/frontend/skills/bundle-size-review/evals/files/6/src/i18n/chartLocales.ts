// Register ECharts locales up front so chart tooltips/toolbox text match the UI language.
// Added in TPO-388 when we started the localisation work.
import { registerLocale } from 'echarts/core'
import langDE from 'echarts/lib/i18n/langDE.js'
import langFR from 'echarts/lib/i18n/langFR.js'
import langES from 'echarts/lib/i18n/langES.js'
import langJA from 'echarts/lib/i18n/langJA.js'
import langPTbr from 'echarts/lib/i18n/langPT-br.js'
import langKO from 'echarts/lib/i18n/langKO.js'

registerLocale('DE', langDE)
registerLocale('FR', langFR)
registerLocale('ES', langES)
registerLocale('JA', langJA)
registerLocale('PT-br', langPTbr)
registerLocale('KO', langKO)
