//! Internal tooling crate with `publish = false`.

/// Offsets the core answer for internal use.
pub fn offset() -> u32 {
    gac_example_core::answer() + 1
}

#[cfg(test)]
mod tests {
    #[test]
    fn offsets_the_core_answer() {
        assert_eq!(super::offset(), 43);
    }
}
