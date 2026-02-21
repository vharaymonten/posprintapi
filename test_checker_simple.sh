#!/bin/bash

# Simple Checker Order Test with Notes

API_URL="http://localhost:9191/api/v1/initiate-print"

echo "========================================="
echo "Simple Checker Order with Notes"
echo "========================================="
echo ""

# Prompt for printer code
read -p "Enter printer code [CHECKER]: " PRINTER_CODE
PRINTER_CODE=${PRINTER_CODE:-CHECKER}

echo ""
echo "Using printer: $PRINTER_CODE"
echo ""

# Simple Checker Order
echo "Sending checker order..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"checker.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"order_no\": \"ORD-001\",
      \"table_no\": \"5\",
      \"customer_name\": \"John Doe\",
      \"items\": [
        {\"name\": \"Nasi Goreng\", \"qty\": 1, \"note\": \"Extra spicy\"},
        {\"name\": \"Iced Tea\", \"qty\": 2, \"note\": \"Less sugar\"},
        {\"name\": \"Spring Rolls\", \"qty\": 1}
      ],
      \"checker_note\": \"Customer prefers quick service\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo "Order sent successfully!"
echo "========================================="
