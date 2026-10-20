// Renders the one-line title a user types above a comment on a note.
import { renderInline } from "quillmark";

export function renderCommentTitle(title) {
  return renderInline(title.trim());
}
