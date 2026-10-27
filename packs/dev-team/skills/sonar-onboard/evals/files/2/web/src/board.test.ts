import { formatRow } from "./board";

test("due when zero minutes", () => {
  expect(formatRow({ route: "7", minutes: 0 })).toBe("7  due");
});

test("minutes otherwise", () => {
  expect(formatRow({ route: "12", minutes: 4 })).toBe("12  4 min");
});
