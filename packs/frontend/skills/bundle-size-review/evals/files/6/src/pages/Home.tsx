import { Link } from 'react-router-dom'
import { messages } from '../i18n'
import { useLocale } from '../i18n/useLocale'

export default function Home() {
  const lang = useLocale()
  const t = messages[lang]
  return (
    <main>
      <h1>{t['home.title']}</h1>
      <Link to="/reports">{t['home.cta']}</Link>
    </main>
  )
}
