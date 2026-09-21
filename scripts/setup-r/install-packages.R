args <- commandArgs(trailingOnly = TRUE)
packages <- args[1]
cran_mirror <- args[2]
working_directory <- args[3]

if (!nzchar(working_directory)) {
  working_directory <- "."
}
setwd(working_directory)

pkg_vec <- unlist(strsplit(packages, "[,\\n ]+"))
pkg_vec <- pkg_vec[nzchar(pkg_vec)]
if (length(pkg_vec)) {
  install.packages(pkg_vec, repos = cran_mirror)
}
