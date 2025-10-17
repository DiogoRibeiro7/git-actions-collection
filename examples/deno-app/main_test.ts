import { add } from "./main.ts";

function assertEquals(actual: unknown, expected: unknown): void {
  if (actual !== expected) {
    throw new Error(`Expected ${expected}, got ${actual}`);
  }
}

Deno.test("add", () => {
  assertEquals(add(2, 3), 5);
});
