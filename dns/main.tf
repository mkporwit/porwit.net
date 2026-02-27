# Configure the Azure provider
terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = ">= 3.88.0"
    }
  }
}

provider "azurerm" {
  tenant_id = "5f1b609b-f2ef-4643-a88e-43407da4cf15"
  subscription_id = "22493fdc-7538-4b01-94ea-72d0189525c3"
  skip_provider_registration = true

  features {}
}

resource "azurerm_resource_group" "infra" {
  name     = var.resource_group_name
  location = var.availability_zone_name
}

resource "azurerm_dns_zone" "top-level" {
  name    = var.domain_name
  resource_group_name = var.resource_group_name
}
 
resource "azurerm_dns_txt_record" "spf" {
  name      = "@"
  zone_name = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl       =   300

  record {
    value = "v=spf1 include:_spf.google.com ~all"
  }
}

resource "azurerm_dns_txt_record" "google-domainkey" {
  name                = "google._domainkey"
  zone_name           = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl                 = 300

  record {
    value = "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCLmKKE3UCTEry961fLlBuA+dreYKYV1kdW3C/qlMX/An9zjAHg6pNPSk612WrdTFVyb78+sgReXurdtaJzy+l0HZP+2AfBMCSRtm9MChvdCPxGDqhKd0xydyPIArhmdCnwKEW8+DSW7MTu7PT/9CdBEABotQbd2Zmky8/fPo5XeQIDAQAB"
  }
}

resource "azurerm_dns_txt_record" "dmarc" {
  name                = "_dmarc"
  zone_name           = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl                 = 300

  record {
    value = "v=DMARC1; p=none; rua=mailto:mkporwit+dmarc@porwit.net"
  }
}

resource "azurerm_dns_cname_record" "mail" {
  name                = "mail"
  zone_name           = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl                 = 3600
  record              = "ghs.googlehosted.com"
}

resource "azurerm_dns_mx_record" "mx" {
  zone_name = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl = 300
  record {
    preference = 1
    exchange = "aspmx.l.google.com"
  }

    record {
    preference = 5
    exchange = "alt1.aspmx.l.google.com"
  }

  record {
    preference = 5
    exchange = "alt2.aspmx.l.google.com"
  }

  record {
    preference = 10
    exchange = "aspmx2.googlemail.com"
  }

  record {
    preference = 10
    exchange = "aspmx3.googlemail.com"
  }
}


# --- jobtracker ---

resource "azurerm_dns_cname_record" "jobtracker" {
  name                = "jobtracker"
  zone_name           = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl                 = 3600
  record              = "d2dwxp94buikfp.cloudfront.net"
}

resource "azurerm_dns_cname_record" "jobtracker-acm-validation" {
  name                = "_4d31a7663683b9bc703926ff8ae94b06.jobtracker"
  zone_name           = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl                 = 3600
  record              = "_a3aa780514ee68ac9177e088187db5d4.jkddzztszm.acm-validations.aws."
}

# --- gunset ---

resource "azurerm_dns_cname_record" "gunset" {
  name                = "gunset"
  zone_name           = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl                 = 3600
  record              = "d1j75d6mvqsxpz.cloudfront.net"
}

resource "azurerm_dns_cname_record" "gunset-acm-validation" {
  name                = "_cbf5fba40b3b97f1b1b2d0944dbf9c44.gunset"
  zone_name           = azurerm_dns_zone.top-level.name
  resource_group_name = var.resource_group_name
  ttl                 = 3600
  record              = "_10ac216bbe66079118d8316404b270c5.jkddzztszm.acm-validations.aws."
}
