terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "example" {
  bucket = "example-bucket-${var.region}"
}

variable "region" {
  default = "us-east-1"
}
