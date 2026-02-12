package com.example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class AppTest {
    @Test
    void adds() {
        assertEquals(4, App.add(2, 2));
        assertEquals(0, App.add(0, 0));
        assertEquals(3, App.add(-2, 5));
        assertEquals(-10, App.add(-3, -7));
    }

    @Test
    void isCommutative() {
        assertEquals(App.add(9, -4), App.add(-4, 9));
    }
}
