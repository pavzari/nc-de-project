terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.21.0"
    }
  }

  backend "s3" {
    bucket = "nc-de-project-backend-bucket"
    key    = "terraform.tfstate" 
    region = "eu-west-2"
  }
}

provider "aws" {
  region  = "eu-west-2"
  profile = "pav"
}
