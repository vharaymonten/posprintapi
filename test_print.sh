#!/bin/bash

# Printer API Test Script
# Test kitchen and receipt templates

API_URL="http://localhost:9191/api/v1/initiate-print"

echo "========================================="
echo "Printer API - Test Script"
echo "========================================="
echo ""

# Test 1: Kitchen Template
echo "[1] Testing Kitchen Template..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "kitchen.txt",
    "printer_code": "KITCHEN",
    "metadata": {
      "order_no": "ORD-12345",
      "table_no": "7",
      "customer_name": "John Doe",
      "items": [
        {"name": "Margherita Pizza", "qty": 2},
        {"name": "Caesar Salad", "qty": 1},
        {"name": "Garlic Bread", "qty": 3}
      ],
      "kitchen_note": "Extra cheese on pizza\nNo croutons on salad"
    }
  }'

echo ""
echo ""
echo "========================================="
echo ""

# Test 2: Receipt Template
echo "[2] Testing Receipt Template..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "receipt.txt",
    "printer_code": "BAR",
    "metadata": {
      "store_name": "ANEKA Restoran",
      "address_line_1": "Jl. Raya No. 123",
      "address_line_2": "Kelurahan ABC",
      "city_line": "Jakarta Selatan, DKI Jakarta",
      "npwp": "01.234.567.8-901.000",
      "phone": "+62 21 1234567",
      "email": "info@anekarestoran.com",
      "tagline": "Authentic Indonesian Cuisine",
      "date": "2026-02-21",
      "time": "14:35:22",
      "invoice_no": "INV-2026-0221-001",
      "cashier_label": "Cashier: Alice",
      "items": [
        {
          "prefix": "1.",
          "name": "Nasi Goreng Special",
          "qty": 2,
          "price": "45,000"
        },
        {
          "prefix": "2.",
          "name": "Es Teh Manis",
          "qty": 2,
          "price": "10,000"
        },
        {
          "prefix": "3.",
          "name": "Sate Ayam (10 tusuk)",
          "qty": 1,
          "price": "35,000"
        }
      ],
      "total": "100,000",
      "tax": "10,000",
      "cash": "150,000",
      "change": "40,000",
      "total_items": 3,
      "total_qty": 5,
      "points": 100
    }
  }'

echo ""
echo ""
echo "========================================="
echo ""

# Test 3: Receipt Preview (without printer)
echo "[3] Testing Receipt Preview (no printer)..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "receipt.txt",
    "metadata": {
      "store_name": "Quick Test",
      "date": "2026-02-21",
      "time": "15:00",
      "invoice_no": "TEST-001",
      "cashier_label": "Cashier: System",
      "items": [
        {
          "prefix": "1.",
          "name": "Test Item",
          "qty": 1,
          "price": "10,000"
        }
      ],
      "total": "10,000",
      "tax": "1,000",
      "cash": "20,000",
      "change": "9,000",
      "total_items": 1,
      "total_qty": 1,
      "points": 10,
      "npwp": "00.000.000.0-000.000",
      "phone": "0000-0000",
      "email": "test@test.com",
      "address_line_1": "Test Address",
      "address_line_2": "",
      "city_line": "Test City",
      "tagline": "Test Tagline"
    }
  }'

echo ""
echo ""
echo "========================================="
echo "Tests Complete!"
echo "========================================="
