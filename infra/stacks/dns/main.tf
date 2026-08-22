terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "jobtracker-tfstate-569397624996"
    key            = "dns/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "jobtracker-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-west-2"
}

# --- Route 53 Zone ---

resource "aws_route53_zone" "porwit_net" {
  name = "porwit.net"
}

# --- Email Records ---

# MX records (Google Workspace)
resource "aws_route53_record" "mx" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "porwit.net"
  type    = "MX"
  ttl     = 3600

  records = [
    "1 aspmx.l.google.com",
    "5 alt1.aspmx.l.google.com",
    "5 alt2.aspmx.l.google.com",
    "10 aspmx2.googlemail.com",
    "10 aspmx3.googlemail.com",
  ]
}

# SPF record
resource "aws_route53_record" "spf" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "porwit.net"
  type    = "TXT"
  ttl     = 300

  records = [
    "v=spf1 include:_spf.google.com ~all",
  ]
}

# DKIM record
resource "aws_route53_record" "dkim" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "google._domainkey.porwit.net"
  type    = "TXT"
  ttl     = 300

  records = [
    "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCLmKKE3UCTEry961fLlBuA+dreYKYV1kdW3C/qlMX/An9zjAHg6pNPSk612WrdTFVyb78+sgReXurdtaJzy+l0HZP+2AfBMCSRtm9MChvdCPxGDqhKd0xydyPIArhmdCnwKEW8+DSW7MTu7PT/9CdBEABotQbd2Zmky8/fPo5XeQIDAQAB",
  ]
}

# DMARC record
resource "aws_route53_record" "dmarc" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "_dmarc.porwit.net"
  type    = "TXT"
  ttl     = 300

  records = [
    "v=DMARC1; p=none; pct=100; rua=mailto:re+xtkshmydec8@dmarc.postmarkapp.com; sp=none; aspf=r;",
  ]
}

# Google Workspace mail CNAME
resource "aws_route53_record" "mail" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "mail.porwit.net"
  type    = "CNAME"
  ttl     = 3600

  records = ["ghs.googlehosted.com"]
}

# --- JobTracker ---

# A alias record pointing to CloudFront
resource "aws_route53_record" "jobtracker" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "jobtracker.porwit.net"
  type    = "A"

  alias {
    name                   = "d2dwxp94buikfp.cloudfront.net"
    zone_id                = "Z2FDTNDATAQYW2" # CloudFront hosted zone ID (global constant)
    evaluate_target_health = false
  }
}

# ACM validation CNAME for jobtracker
resource "aws_route53_record" "jobtracker_acm_validation" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "_4d31a7663683b9bc703926ff8ae94b06.jobtracker.porwit.net"
  type    = "CNAME"
  ttl     = 3600

  records = ["_a3aa780514ee68ac9177e088187db5d4.jkddzztszm.acm-validations.aws."]
}

# --- Gunset ---

# A alias record pointing to CloudFront
resource "aws_route53_record" "gunset" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "gunset.porwit.net"
  type    = "A"

  alias {
    name                   = "d1j75d6mvqsxpz.cloudfront.net"
    zone_id                = "Z2FDTNDATAQYW2" # CloudFront hosted zone ID (global constant)
    evaluate_target_health = false
  }
}

# ACM validation CNAME for gunset
resource "aws_route53_record" "gunset_acm_validation" {
  zone_id = aws_route53_zone.porwit_net.zone_id
  name    = "_cbf5fba40b3b97f1b1b2d0944dbf9c44.gunset.porwit.net"
  type    = "CNAME"
  ttl     = 3600

  records = ["_10ac216bbe66079118d8316404b270c5.jkddzztszm.acm-validations.aws."]
}
