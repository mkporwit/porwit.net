resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = var.hash_key
  range_key = var.range_key

  attribute {
    name = var.hash_key
    type = "S"
  }

  attribute {
    name = var.range_key
    type = "S"
  }

  dynamic "attribute" {
    for_each = var.additional_attributes
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  dynamic "global_secondary_index" {
    for_each = var.global_secondary_indexes
    content {
      name            = global_secondary_index.value.name
      hash_key        = global_secondary_index.value.hash_key
      range_key       = lookup(global_secondary_index.value, "range_key", null)
      projection_type = lookup(global_secondary_index.value, "projection_type", "ALL")
    }
  }

  dynamic "ttl" {
    for_each = var.ttl_attribute != null ? [var.ttl_attribute] : []
    content {
      attribute_name = ttl.value
      enabled        = true
    }
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }
}
