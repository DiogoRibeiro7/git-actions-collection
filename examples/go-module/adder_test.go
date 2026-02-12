package gomodule

import "testing"

func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a        int
        b        int
        expected int
    }{
        {"adds positives", 2, 2, 4},
        {"adds zeros", 0, 0, 0},
        {"mixes signs", -2, 5, 3},
        {"adds negatives", -3, -7, -10},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            if Add(tt.a, tt.b) != tt.expected {
                t.Fatalf("expected %d", tt.expected)
            }
        })
    }
}

func TestAddCommutative(t *testing.T) {
    if Add(9, -4) != Add(-4, 9) {
        t.Fatalf("expected commutative result")
    }
}
