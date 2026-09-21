config_file <- commandArgs(trailingOnly = TRUE)[1]
target_input <- commandArgs(trailingOnly = TRUE)[2]
working_directory <- commandArgs(trailingOnly = TRUE)[3]

if (!nzchar(working_directory)) {
  working_directory <- "."
}
setwd(working_directory)

options(error = function(e) { message(conditionMessage(e)); quit(status = 1) })
suppressPackageStartupMessages(library(lintr))

if (nzchar(config_file)) {
  message(sprintf("Using lintr config: %s", config_file))
  Sys.setenv(LINTR_CONFIG = config_file)
}

if (!nzchar(target_input)) {
  target_input <- "R"
}

targets <- unlist(strsplit(target_input, "[,\\n ]+"))
targets <- targets[nzchar(targets)]
if (!length(targets)) {
  targets <- c("R")
}

lint_results <- lapply(targets, function(path) {
  if (dir.exists(path)) {
    lintr::lint_dir(path = path, parse_settings = TRUE)
  } else if (file.exists(path)) {
    lintr::lint(path = path, parse_settings = TRUE)
  } else {
    message(sprintf("Target '%s' not found. Skipping.", path))
    structure(list(), class = "lintr_lints")
  }
})

total_lints <- sum(vapply(lint_results, length, integer(1)))
if (total_lints > 0) {
  invisible(lapply(lint_results, function(lints) {
    if (length(lints)) print(lints)
  }))
  stop(sprintf("lintr found %d issue(s).", total_lints))
}

message("lintr completed without findings.")
