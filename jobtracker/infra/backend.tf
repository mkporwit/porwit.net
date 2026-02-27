terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.82.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket         = "jobtracker-tfstate-569397624996"
    key            = "jobtracker/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "jobtracker-tflock"
    encrypt        = true
  }
}
