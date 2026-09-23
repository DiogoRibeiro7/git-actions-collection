//! Core library published before the crates that depend on it.

/// Returns the value shared by the workspace crates.
pub fn answer() -> u32 {
    42
}

#[cfg(test)]
mod tests {
    #[test]
    fn answers() {
        assert_eq!(super::answer(), 42);
    }
}
