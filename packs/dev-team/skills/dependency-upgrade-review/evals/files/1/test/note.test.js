import { describe, expect, it } from "vitest";
import { renderNoteBody } from "../src/render/note.js";

describe("renderNoteBody", () => {
  it("renders bold text", () => {
    expect(renderNoteBody("**ship it**")).toBe("<p><strong>ship it</strong></p>\n");
  });

  it("keeps single line breaks", () => {
    expect(renderNoteBody("a\nb")).toBe("<p>a<br>\nb</p>\n");
  });
});
