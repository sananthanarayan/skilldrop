import { Button } from '@quillmark/ui'

export default function Home() {
  return (
    <main>
      <h1>New this week</h1>
      <Button onClick={() => (window.location.href = '/p/QM-1042')}>Shop the notebook</Button>
    </main>
  )
}
