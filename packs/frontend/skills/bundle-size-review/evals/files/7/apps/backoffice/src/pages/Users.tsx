import { Button, DataGrid, DatePicker } from '@quillmark/ui'
import { useState } from 'react'

export default function Users() {
  const [since, setSince] = useState<string | null>(null)
  return (
    <section>
      <DatePicker value={since} onChange={setSince} label="Joined since" />
      <DataGrid source="/api/users" filter={{ since }} />
      <Button variant="secondary">Export</Button>
    </section>
  )
}
