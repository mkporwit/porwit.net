resource "aws_cloudwatch_event_rule" "daily_scan" {
  name                = "jobtracker-daily-scan"
  description         = "Daily career page scan at 6am PT"
  schedule_expression = "cron(0 14 * * ? *)"
}

resource "aws_cloudwatch_event_target" "scanner" {
  rule = aws_cloudwatch_event_rule.daily_scan.name
  arn  = aws_lambda_function.scanner.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scanner.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_scan.arn
}
