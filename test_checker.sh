#!/bin/bash

# Test Checker/Waiter Template

API_URL="http://localhost:9191/api/v1/initiate-print"

echo "========================================="
echo "Test Checker/Waiter Template"
echo "========================================="
echo ""

# Prompt for printer code
read -p "Enter printer code [CHECKER]: " PRINTER_CODE
PRINTER_CODE=${PRINTER_CODE:-CHECKER}

echo ""
echo "Using printer: $PRINTER_CODE"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Test 1: Simple Checker Order
echo "[1] Testing Simple Checker Order..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"checker.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"order_no\": \"ORD-20260221-001\",
      \"table_no\": \"7\",
      \"customer_name\": \"Budi Santoso\",
      \"items\": [
        {\"name\": \"Nasi Goreng Special\", \"qty\": 2, \"note\": \"Pedas sedang, tanpa terasi\"},
        {\"name\": \"Sate Ayam (10 tusuk)\", \"qty\": 1},
        {\"name\": \"Gado-Gado\", \"qty\": 1},
        {\"name\": \"Es Teh Manis\", \"qty\": 2, \"note\": \"Gula sedikit\"}
      ],
      \"checker_note\": \"Customer allergic to peanuts\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo ""

# Test 2: Checker Order with Special Requirements
echo "[2] Testing Checker Order with Special Requirements..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"checker.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"order_no\": \"ORD-20260221-015\",
      \"table_no\": \"VIP-3\",
      \"customer_name\": \"Mrs. Anderson\",
      \"items\": [
        {\"name\": \"Caesar Salad\", \"qty\": 2, \"note\": \"No croutons, dressing on side\"},
        {\"name\": \"Grilled Salmon\", \"qty\": 1, \"note\": \"Well done\"},
        {\"name\": \"Ribeye Steak\", \"qty\": 1, \"note\": \"Medium rare\"},
        {\"name\": \"Mineral Water\", \"qty\": 3}
      ],
      \"checker_note\": \"VIP Customer - Priority Service\\nBirthday celebration - prepare candle\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo ""

# Test 3: Large Table Order
echo "[3] Testing Large Table Order..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"checker.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"order_no\": \"ORD-20260221-025\",
      \"table_no\": \"12\",
      \"customer_name\": \"Group Reservation\",
      \"items\": [
        {\"name\": \"Nasi Goreng\", \"qty\": 5},
        {\"name\": \"Mie Goreng\", \"qty\": 3},
        {\"name\": \"Ayam Goreng\", \"qty\": 4},
        {\"name\": \"Sate Ayam\", \"qty\": 8, \"note\": \"4 pedas, 4 tidak pedas\"},
        {\"name\": \"Gado-Gado\", \"qty\": 2},
        {\"name\": \"Es Teh Manis\", \"qty\": 6},
        {\"name\": \"Es Jeruk\", \"qty\": 4}
      ],
      \"checker_note\": \"Large group - 10 people\\nServe together please\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo "All tests completed!"
echo "========================================="
