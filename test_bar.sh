#!/bin/bash

# Test Bar Template

API_URL="http://localhost:9191/api/v1/initiate-print"

echo "========================================="
echo "Test Bar Template"
echo "========================================="
echo ""

# Prompt for printer code
read -p "Enter printer code [BAR]: " PRINTER_CODE
PRINTER_CODE=${PRINTER_CODE:-BAR}

echo ""
echo "Using printer: $PRINTER_CODE"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# # Test 1: Simple Bar Order
# echo "[1] Testing Simple Bar Order..."
# curl -X POST "$API_URL" \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"template_name\": \"bar.txt\",
#     \"printer_code\": \"$PRINTER_CODE\",
#     \"metadata\": {
#       \"order_no\": \"BAR-001\",
#       \"table_no\": \"12\",
#       \"server_name\": \"Alice\",
#       \"time\": \"20:15:30\",
#       \"items\": [
#         {\"qty\": 2, \"name\": \"Mojito\"},
#         {\"qty\": 1, \"name\": \"Margarita\"},
#         {\"qty\": 3, \"name\": \"Beer Bintang\"}
#       ],
#       \"total_qty\": 6,
#       \"time_ordered\": \"20:15\"
#     }
#   }"

# echo ""
# echo ""
# echo "========================================="
# echo ""

# Test 2: Bar Order with Special Notes
echo "[2] Testing Bar Order with Notes..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"bar.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"order_no\": \"BAR-002\",
      \"table_no\": \"7\",
      \"server_name\": \"Bob\",
      \"time\": \"21:30:00\",
      \"items\": [
        {\"qty\": 1, \"name\": \"Long Island Ice Tea\", \"note\": \"Extra lime\"},
        {\"qty\": 2, \"name\": \"Whiskey Sour\", \"note\": \"No ice\"},
        {\"qty\": 1, \"name\": \"Cosmopolitan\"},
        {\"qty\": 2, \"name\": \"Vodka Martini\", \"note\": \"Shaken not stirred\"}
      ],
      \"total_qty\": 6,
      \"special_note\": \"VIP Table - Priority Service\",
      \"time_ordered\": \"21:30\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo ""

# # Test 3: Large Bar Order
# echo "[3] Testing Large Bar Order..."
# curl -X POST "$API_URL" \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"template_name\": \"bar.txt\",
#     \"printer_code\": \"$PRINTER_CODE\",
#     \"metadata\": {
#       \"order_no\": \"BAR-003\",
#       \"table_no\": \"VIP-1\",
#       \"server_name\": \"Charlie\",
#       \"time\": \"22:00:15\",
#       \"items\": [
#         {\"qty\": 4, \"name\": \"Heineken\"},
#         {\"qty\": 2, \"name\": \"Corona Extra\"},
#         {\"qty\": 1, \"name\": \"Guinness Draft\"},
#         {\"qty\": 3, \"name\": \"Mojito\"},
#         {\"qty\": 2, \"name\": \"Piña Colada\"},
#         {\"qty\": 1, \"name\": \"Bloody Mary\", \"note\": \"Extra spicy\"},
#         {\"qty\": 2, \"name\": \"Tequila Sunrise\"},
#         {\"qty\": 5, \"name\": \"Soft Drink (Coke)\"}
#       ],
#       \"total_qty\": 20,
#       \"special_note\": \"Party Group - Serve together\",
#       \"time_ordered\": \"22:00\"
#     }
#   }"

# echo ""
# echo ""
# echo "========================================="
# echo ""

# # Test 4: Bar Order - Mixed Drinks & Bottles
# echo "[4] Testing Mixed Drinks & Bottles..."
# curl -X POST "$API_URL" \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"template_name\": \"bar.txt\",
#     \"printer_code\": \"$PRINTER_CODE\",
#     \"metadata\": {
#       \"order_no\": \"BAR-004\",
#       \"table_no\": \"15\",
#       \"server_name\": \"Diana\",
#       \"time\": \"23:15:00\",
#       \"items\": [
#         {\"qty\": 1, \"name\": \"Negroni\"},
#         {\"qty\": 1, \"name\": \"Old Fashioned\"},
#         {\"qty\": 2, \"name\": \"Singapore Sling\"},
#         {\"qty\": 1, \"name\": \"Wine - Chardonnay\", \"note\": \"Bottle\"},
#         {\"qty\": 3, \"name\": \"Espresso Martini\", \"note\": \"Double shot\"},
#         {\"qty\": 2, \"name\": \"Aperol Spritz\"}
#       ],
#       \"total_qty\": 10,
#       \"time_ordered\": \"23:15\"
#     }
#   }"

# echo ""
# echo ""
# echo "========================================="
# echo "Tests Complete!"
# echo "========================================="
