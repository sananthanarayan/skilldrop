// Renders the Markdown body of a shared team note. Bodies are written by any team member.
import quillmark, { setOptions } from "quillmark";

setOptions({ breaks: true });

export function renderNoteBody(markdown) {
  return quillmark.render(markdown);
}
