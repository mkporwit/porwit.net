# --- SES domain identity for magic-link emails ---
# Domain identity covers FROM_EMAIL (mkporwit@porwit.net) and any @porwit.net
# sender. Easy DKIM: the identity generates 3 CNAME tokens we publish to route53,
# so verification + DKIM signing happen with no manual click-link step.
# ponytail: no custom MAIL FROM domain — SPF (Google) + DKIM is enough for
# transactional deliverability; add a MAIL FROM subdomain only if BIMI/strict
# alignment is ever needed.

data "aws_route53_zone" "porwit" {
  name = "porwit.net"
}

resource "aws_sesv2_email_identity" "porwit_net" {
  email_identity = "porwit.net"
}

# Easy DKIM publishes 3 CNAMEs: <token>._domainkey -> <token>.dkim.amazonses.com
resource "aws_route53_record" "ses_dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.porwit.zone_id
  name    = "${aws_sesv2_email_identity.porwit_net.dkim_signing_attributes[0].tokens[count.index]}._domainkey.porwit.net"
  type    = "CNAME"
  ttl     = 1800
  records = ["${aws_sesv2_email_identity.porwit_net.dkim_signing_attributes[0].tokens[count.index]}.dkim.amazonses.com"]
}
