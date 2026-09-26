"""Consumer fixture for the benchmark-smoke self-test."""


def fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def test_fib(benchmark) -> None:
    assert benchmark(fib, 20) == 6765
