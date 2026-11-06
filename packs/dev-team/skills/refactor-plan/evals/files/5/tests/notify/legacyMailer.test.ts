import { render } from "../../src/notify/legacyMailer";

describe("render", () => {
  it("substitutes vars", () => {
    expect(render("Hi {{ name }}", { name: "Ada" })).toBe("Hi Ada");
  });
});
