args <- commandArgs(trailingOnly = TRUE)
test_dir <- args[1]
install_deps_raw <- args[2]
use_devtools_raw <- args[3]
working_directory <- args[4]

if (!nzchar(working_directory)) {
  working_directory <- "."
}
setwd(working_directory)

options(error = function(e) { message(conditionMessage(e)); quit(status = 1) })
suppressPackageStartupMessages(library(testthat))

install_deps <- identical(tolower(install_deps_raw), "true")
use_devtools <- identical(tolower(use_devtools_raw), "true")

if (install_deps && file.exists("DESCRIPTION")) {
  message("Installing package dependencies via remotes::install_deps().")
  remotes::install_deps(dependencies = TRUE)
}

if (file.exists("DESCRIPTION") && use_devtools) {
  message("Running devtools::test() for package tests.")
  if (!requireNamespace("devtools", quietly = TRUE)) {
    stop("devtools package is required when use-devtools is true and DESCRIPTION exists.")
  }
  devtools::test()
} else if (dir.exists(test_dir)) {
  message(sprintf("Running testthat::test_dir() on %s", test_dir))
  testthat::test_dir(test_dir, reporter = "summary")
} else {
  message(sprintf("No tests found in '%s' and no DESCRIPTION file detected. Skipping.", test_dir))
}
