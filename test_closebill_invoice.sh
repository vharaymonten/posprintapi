#!/bin/bash

# Test CloseBill and Invoice Templates

API_URL="http://localhost:9191/api/v1/initiate-print"

echo "========================================="
echo "Test CloseBill & Invoice Templates"
echo "========================================="
echo ""

# Prompt for printer code
read -p "Enter printer code [KITCHEN]: " PRINTER_CODE
PRINTER_CODE=${PRINTER_CODE:-KITCHEN}

echo ""
echo "Using printer: $PRINTER_CODE"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Test 1: CloseBill Template
echo "[1] Testing CloseBill Template..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"closebill.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"store_name\": \"ANEKA Restoran\",
      \"address_line_1\": \"Jl. Sudirman No. 123\",
      \"address_line_2\": \"Kelurahan Senayan\",
      \"city_line\": \"Jakarta Selatan, DKI Jakarta 12190\",
      \"npwp\": \"01.234.567.8-901.000\",
      \"phone\": \"+62 21 5551234\",
      \"email\": \"info@anekarestoran.com\",
      \"date\": \"2026-02-21\",
      \"time\": \"20:15:30\",
      \"bill_no\": \"BILL-2026-0221-0089\",
      \"table_no\": \"12\",
      \"cashier_label\": \"Kasir: Siti\",
      \"items\": [
        {
          \"prefix\": \"1.\",
          \"name\": \"Nasi Goreng Special\",
          \"qty\": 2,
          \"price\": \"Rp 90.000\"
        },
        {
          \"prefix\": \"2.\",
          \"name\": \"Sate Ayam (10 tusuk)\",
          \"qty\": 1,
          \"price\": \"Rp 35.000\"
        },
        {
          \"prefix\": \"3.\",
          \"name\": \"Es Teh Manis\",
          \"qty\": 3,
          \"price\": \"Rp 15.000\"
        }
      ],
      \"subtotal\": \"Rp 140.000\",
      \"tax\": \"Rp 14.000\",
      \"discount\": \"Rp 5.000\",
      \"total\": \"Rp 149.000\",
      \"payments\": [
        {\"type\": \"Cash\", \"amount\": \"Rp 100.000\"},
        {\"type\": \"Card (Visa)\", \"amount\": \"Rp 49.000\"}
      ],
      \"total_payment\": \"Rp 149.000\",
      \"change\": \"Rp 0\",
      \"total_items\": 3,
      \"total_qty\": 6,
      \"tagline\": \"Terima Kasih\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo ""

# Test 2: CloseBill with Cash Payment Only
echo "[2] Testing CloseBill (Cash Only)..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"closebill.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"store_name\": \"WARUNG MAKAN SEDERHANA\",
      \"address_line_1\": \"Jl. Kebon Sirih No. 45\",
      \"address_line_2\": \"Menteng\",
      \"city_line\": \"Jakarta Pusat 10340\",
      \"npwp\": \"02.345.678.9-012.000\",
      \"phone\": \"+62 21 3141234\",
      \"email\": \"warung@email.com\",
      \"date\": \"2026-02-21\",
      \"time\": \"21:00:00\",
      \"bill_no\": \"BILL-2026-0221-0090\",
      \"table_no\": \"5\",
      \"cashier_label\": \"Kasir: Ahmad\",
      \"items\": [
        {\"prefix\": \"1.\", \"name\": \"Ayam Goreng\", \"qty\": 1, \"price\": \"Rp 25.000\"},
        {\"prefix\": \"2.\", \"name\": \"Nasi Putih\", \"qty\": 1, \"price\": \"Rp 5.000\"},
        {\"prefix\": \"3.\", \"name\": \"Es Jeruk\", \"qty\": 1, \"price\": \"Rp 8.000\"}
      ],
      \"subtotal\": \"Rp 38.000\",
      \"tax\": \"Rp 3.800\",
      \"total\": \"Rp 41.800\",
      \"payments\": [
        {\"type\": \"Cash\", \"amount\": \"Rp 50.000\"}
      ],
      \"total_payment\": \"Rp 50.000\",
      \"change\": \"Rp 8.200\",
      \"total_items\": 3,
      \"total_qty\": 3,
      \"tagline\": \"Sampai Jumpa Lagi\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo ""

# Test 3: Invoice Template
echo "[3] Testing Invoice Template..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"invoice.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"store_name\": \"ANEKA Catering Services\",
      \"address_line_1\": \"Jl. Gatot Subroto No. 88\",
      \"address_line_2\": \"Kuningan\",
      \"city_line\": \"Jakarta Selatan 12950\",
      \"npwp\": \"03.456.789.0-123.000\",
      \"phone\": \"+62 21 5558888\",
      \"email\": \"invoice@anekacatering.com\",
      \"website\": \"www.anekacatering.com\",
      \"invoice_no\": \"INV-2026-0221-0456\",
      \"date\": \"2026-02-21\",
      \"time\": \"10:00:00\",
      \"due_date\": \"2026-03-07\",
      \"customer_name\": \"PT. Maju Bersama\",
      \"customer_address\": \"Jl. Thamrin No. 45, Jakarta\",
      \"customer_phone\": \"+62 21 3334444\",
      \"items\": [
        {
          \"no\": \"1\",
          \"name\": \"Paket Nasi Box (50 pax)\",
          \"qty\": 50,
          \"unit_price\": \"Rp 35.000\",
          \"amount\": \"Rp 1.750.000\"
        },
        {
          \"no\": \"2\",
          \"name\": \"Snack Box (50 pax)\",
          \"qty\": 50,
          \"unit_price\": \"Rp 25.000\",
          \"amount\": \"Rp 1.250.000\"
        },
        {
          \"no\": \"3\",
          \"name\": \"Mineral Water (100 btl)\",
          \"qty\": 100,
          \"unit_price\": \"Rp 5.000\",
          \"amount\": \"Rp 500.000\"
        }
      ],
      \"subtotal\": \"Rp 3.500.000\",
      \"tax_rate\": \"11\",
      \"tax\": \"Rp 385.000\",
      \"service_charge\": \"Rp 175.000\",
      \"total\": \"Rp 4.060.000\",
      \"payment_status\": \"UNPAID\",
      \"payment_method\": \"Bank Transfer\",
      \"notes\": \"Pembayaran melalui transfer bank\\nBank BCA No: 1234567890\\na.n. PT Aneka Catering\\n\\nMohon konfirmasi setelah transfer\",
      \"tagline\": \"Quality Catering Services\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo ""

# Test 4: Invoice - Paid
echo "[4] Testing Invoice (Paid)..."
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"invoice.txt\",
    \"printer_code\": \"$PRINTER_CODE\",
    \"metadata\": {
      \"store_name\": \"TOKO ELEKTRONIK JAYA\",
      \"address_line_1\": \"Jl. Mangga Besar No. 77\",
      \"address_line_2\": \"Tamansari\",
      \"city_line\": \"Jakarta Barat 11150\",
      \"npwp\": \"04.567.890.1-234.000\",
      \"phone\": \"+62 21 6289999\",
      \"email\": \"sales@tokojaya.com\",
      \"website\": \"www.tokojaya.com\",
      \"invoice_no\": \"INV-2026-0221-9876\",
      \"date\": \"2026-02-21\",
      \"time\": \"14:30:00\",
      \"due_date\": \"2026-02-21\",
      \"customer_name\": \"Budi Santoso\",
      \"customer_phone\": \"+62 812 3456 7890\",
      \"items\": [
        {
          \"no\": \"1\",
          \"name\": \"LED TV 43 inch Samsung\",
          \"qty\": 1,
          \"unit_price\": \"Rp 4.500.000\",
          \"discount\": \"Rp 500.000\",
          \"amount\": \"Rp 4.000.000\"
        },
        {
          \"no\": \"2\",
          \"name\": \"Bracket TV Universal\",
          \"qty\": 1,
          \"unit_price\": \"Rp 150.000\",
          \"amount\": \"Rp 150.000\"
        }
      ],
      \"subtotal\": \"Rp 4.150.000\",
      \"discount\": \"Rp 500.000\",
      \"tax_rate\": \"11\",
      \"tax\": \"Rp 456.500\",
      \"total\": \"Rp 4.606.500\",
      \"payment_status\": \"PAID\",
      \"payment_method\": \"Cash\",
      \"notes\": \"Garansi resmi 1 tahun\\nGratis instalasi\\n\\nBarang yang sudah dibeli\\ntidak dapat ditukar/dikembalikan\",
      \"tagline\": \"Terpercaya Sejak 1995\"
    }
  }"

echo ""
echo ""
echo "========================================="
echo "Tests Complete!"
echo "========================================="
