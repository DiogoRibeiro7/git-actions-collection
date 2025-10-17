terraform {
  required_version = ">= 1.0.0"
}

locals {
  greeting = "hello"
}

output "greeting" {
  value = local.greeting
}
