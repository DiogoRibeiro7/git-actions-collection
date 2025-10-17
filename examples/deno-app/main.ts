export function add(a: number, b: number): number {
  return a + b;
}

if (import.meta.main) {
  console.log(`2 + 3 = ${add(2, 3)}`);
}
