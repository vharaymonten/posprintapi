#!/bin/bash

# Printer API Test Script with Rupiah formatting
# Test kitchen and receipt templates

API_URL="http://localhost:9191/api/v1/initiate-print"

echo "========================================="
echo "Printer API - Test Script (Rupiah)"
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
      "order_no": "ORD-20260221-001",
      "table_no": "7",
      "customer_name": "Budi Santoso",
      "items": [
        {"name": "Nasi Goreng Special", "qty": 2},
        {"name": "Sate Ayam (10 tusuk)", "qty": 1},
        {"name": "Gado-Gado", "qty": 1},
        {"name": "Es Teh Manis", "qty": 2},
        {"name": "Es Jeruk", "qty": 1}
      ],
      "kitchen_note": "Nasi goreng: pedas sedang\nSate: matang sempurna"
    }
  }'

echo ""
echo ""
echo "========================================="
echo ""

# Test 2: Receipt Template with Rupiah
echo "[2] Testing Receipt Template (Rupiah)..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "receipt.txt",
    "printer_code": "BAR",
    "metadata": {
      "store_name": "ANEKA Restoran",
      "address_line_1": "Jl. Sudirman No. 123",
      "address_line_2": "Kelurahan Senayan",
      "city_line": "Jakarta Selatan, DKI Jakarta 12190",
      "npwp": "01.234.567.8-901.000",
      "phone": "+62 21 5551234",
      "email": "info@anekarestoran.com",
      "tagline": "Authentic Indonesian Cuisine",
      "date": "2026-02-21",
      "time": "15:45:30",
      "invoice_no": "INV-2026-0221-0123",
      "cashier_label": "Kasir: Siti",
      "items": [
        {
          "prefix": "1.",
          "name": "Nasi Goreng Special",
          "qty": 2,
          "price": "Rp 90.000"
        },
        {
          "prefix": "2.",
          "name": "Sate Ayam (10 tusuk)",
          "qty": 1,
          "price": "Rp 35.000"
        },
        {
          "prefix": "3.",
          "name": "Gado-Gado",
          "qty": 1,
          "price": "Rp 25.000"
        },
        {
          "prefix": "4.",
          "name": "Es Teh Manis",
          "qty": 2,
          "price": "Rp 10.000"
        },
        {
          "prefix": "5.",
          "name": "Es Jeruk",
          "qty": 1,
          "price": "Rp 8.000"
        }
      ],
      "total": "Rp 168.000",
      "tax": "Rp 16.800",
      "cash": "Rp 200.000",
      "change": "Rp 15.200",
      "total_items": 5,
      "total_qty": 7,
      "points": 168
    }
  }'

echo ""
echo ""
echo "========================================="
echo ""

# Test 3: Large Order Receipt
echo "[3] Testing Large Order Receipt..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "receipt.txt",
    "printer_code": "BAR",
    "metadata": {
      "store_name": "WARUNG PADANG SEDERHANA",
      "address_line_1": "Jl. Kebon Sirih No. 45",
      "address_line_2": "Menteng",
      "city_line": "Jakarta Pusat 10340",
      "npwp": "02.345.678.9-012.000",
      "phone": "+62 21 3141234",
      "email": "warungpadang@email.com",
      "tagline": "Masakan Padang Autentik",
      "date": "2026-02-21",
      "time": "19:30:15",
      "invoice_no": "WPS-2026-0221-0456",
      "cashier_label": "Kasir: Ahmad",
      "items": [
        {
          "prefix": "1.",
          "name": "Rendang Daging",
          "qty": 3,
          "price": "Rp 135.000"
        },
        {
          "prefix": "2.",
          "name": "Ayam Pop",
          "qty": 2,
          "price": "Rp 80.000"
        },
        {
          "prefix": "3.",
          "name": "Gulai Ikan",
          "qty": 1,
          "price": "Rp 45.000"
        },
        {
          "prefix": "4.",
          "name": "Sayur Nangka",
          "qty": 2,
          "price": "Rp 30.000"
        },
        {
          "prefix": "5.",
          "name": "Nasi Putih",
          "qty": 6,
          "price": "Rp 30.000"
        },
        {
          "prefix": "6.",
          "name": "Es Teh Tawar",
          "qty": 3,
          "price": "Rp 15.000"
        },
        {
          "prefix": "7.",
          "name": "Teh Panas",
          "qty": 3,
          "price": "Rp 12.000"
        }
      ],
      "total": "Rp 347.000",
      "tax": "Rp 34.700",
      "cash": "Rp 400.000",
      "change": "Rp 18.300",
      "total_items": 7,
      "total_qty": 20,
      "points": 347
    }
  }'

echo ""
echo ""
echo "========================================="
echo ""

# Test 4: Preview Only (no printer)
echo "[4] Testing Receipt Preview (no printer)..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "receipt.txt",
    "metadata": {
      "store_name": "TEST PREVIEW",
      "date": "2026-02-21",
      "time": "20:00",
      "invoice_no": "PREVIEW-001",
      "cashier_label": "Kasir: System",
      "items": [
        {
          "prefix": "1.",
          "name": "Item Test",
          "qty": 1,
          "price": "Rp 10.000"
        }
      ],
      "total": "Rp 10.000",
      "tax": "Rp 1.000",
      "cash": "Rp 20.000",
      "change": "Rp 9.000",
      "total_items": 1,
      "total_qty": 1,
      "points": 10,
      "npwp": "00.000.000.0-000.000",
      "phone": "0000-0000",
      "email": "test@test.com",
      "address_line_1": "Test Address",
      "address_line_2": "",
      "city_line": "Test City",
      "tagline": "Preview Mode"
    }
  }' | python3 -m json.tool

echo ""
echo ""
echo "========================================="
echo "Tests Complete!"
echo "========================================="
