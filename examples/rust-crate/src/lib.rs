pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn adds() {
        assert_eq!(add(2, 2), 4);
    }

    #[test]
    fn handles_zero_and_negatives() {
        assert_eq!(add(0, 0), 0);
        assert_eq!(add(-2, 5), 3);
        assert_eq!(add(-3, -7), -10);
    }

    #[test]
    fn is_commutative() {
        assert_eq!(add(9, -4), add(-4, 9));
    }
}
