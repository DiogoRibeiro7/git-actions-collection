//! Crate that must be published after `gac-example-core`.

/// Doubles the core answer.
pub fn doubled() -> u32 {
    gac_example_core::answer() * 2
}

#[cfg(test)]
mod tests {
    #[test]
    fn doubles_the_core_answer() {
        assert_eq!(super::doubled(), 84);
    }
}
