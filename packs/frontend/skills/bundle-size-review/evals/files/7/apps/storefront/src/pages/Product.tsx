import { useState } from 'react'
import { Button, PriceTag, Modal } from '@quillmark/ui'

export default function Product() {
  const [open, setOpen] = useState(false)
  return (
    <section>
      <PriceTag amount={2499} currency="EUR" />
      <Button onClick={() => setOpen(true)}>Size guide</Button>
      <Modal open={open} onClose={() => setOpen(false)}>…</Modal>
    </section>
  )
}
