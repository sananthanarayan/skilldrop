import { useState } from 'react';
import RichText from './RichText';
import { postReply } from '../api/client';

// Reply box shown under each ticket on the Home page (PR #482).
export default function CommentBox({ ticketId }) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(null);

  if (!open) {
    return (
      <button className="reply-toggle" onClick={() => setOpen(true)}>
        Reply
      </button>
    );
  }

  return (
    <div className="comment-box">
      <RichText value={value} onChange={setValue} toolbar={['bold', 'italic', 'link']} />
      <button onClick={() => postReply(ticketId, value)}>Send</button>
    </div>
  );
}
