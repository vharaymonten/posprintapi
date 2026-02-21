# Printer API - Template Contracts

API endpoint: `POST /api/v1/initiate-print`

## Base Request Structure

```json
{
  "template_name": "string",
  "printer_code": "string (optional)",
  "printer_id": "string (optional)",
  "metadata": {
    // Template-specific fields
  }
}
```

---

## 1. Kitchen Template (`kitchen.txt`)

### Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_no` | string | Yes | Order number/ID |
| `table_no` | string | Yes | Table number |
| `customer_name` | string | Yes | Customer name |
| `items` | array | Yes | Array of order items |
| `items[].name` | string | Yes | Item name (will be displayed in bold) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].note` | string | No | Special notes for this item |
| `kitchen_note` | string | No | Special instructions for kitchen |

### Example Request

```json
{
  "template_name": "kitchen.txt",
  "printer_code": "KITCHEN",
  "metadata": {
    "order_no": "ORD-20260221-001",
    "table_no": "7",
    "customer_name": "Budi Santoso",
    "items": [
      {"name": "Nasi Goreng Special", "qty": 2, "note": "Pedas sedang, tanpa terasi"},
      {"name": "Sate Ayam (10 tusuk)", "qty": 1},
      {"name": "Es Teh Manis", "qty": 2}
    ],
    "kitchen_note": "Nasi goreng: pedas sedang\nSate: matang sempurna"
  }
}
```

---

## 2. Checker Template (`checker.txt`)

### Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_no` | string | Yes | Order number/ID |
| `table_no` | string | Yes | Table number |
| `customer_name` | string | Yes | Customer name |
| `items` | array | Yes | Array of order items |
| `items[].name` | string | Yes | Item name (will be displayed in bold) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].note` | string | No | Special notes for this item |
| `checker_note` | string | No | Special instructions for checker/waiter |

### Example Request

```json
{
  "template_name": "checker.txt",
  "printer_code": "CHECKER",
  "metadata": {
    "order_no": "ORD-20260221-001",
    "table_no": "7",
    "customer_name": "Budi Santoso",
    "items": [
      {"name": "Nasi Goreng Special", "qty": 2, "note": "Pedas sedang, tanpa terasi"},
      {"name": "Sate Ayam (10 tusuk)", "qty": 1},
      {"name": "Es Teh Manis", "qty": 2}
    ],
    "checker_note": "Customer allergic to peanuts"
  }
}
```

---

## 3. Receipt Template (`receipt.txt`)

### Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `store_name` | string | Yes | Restaurant/store name |
| `address_line_1` | string | Yes | First line of address |
| `address_line_2` | string | No | Second line of address |
| `city_line` | string | Yes | City and postal code |
| `npwp` | string | Yes | Tax ID number (NPWP) |
| `phone` | string | Yes | Contact phone number |
| `email` | string | Yes | Contact email |
| `tagline` | string | No | Store tagline/slogan |
| `date` | string | Yes | Transaction date (YYYY-MM-DD) |
| `time` | string | Yes | Transaction time (HH:MM:SS) |
| `invoice_no` | string | Yes | Invoice/receipt number |
| `cashier_label` | string | Yes | Cashier name (e.g., "Kasir: Alice") |
| `items` | array | Yes | Array of purchased items |
| `items[].prefix` | string | Yes | Item number prefix (e.g., "1.") |
| `items[].name` | string | Yes | Item name (will be displayed in bold) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].price` | string | Yes | Item total price (formatted) |
| `items[].note` | string | No | Special notes for this item |
| `total` | string | Yes | Grand total (formatted with Rp) |
| `tax` | string | Yes | Tax amount (formatted with Rp) |
| `cash` | string | Yes | Cash received (formatted with Rp) |
| `change` | string | Yes | Change returned (formatted with Rp) |
| `total_items` | integer | Yes | Total number of item types |
| `total_qty` | integer | Yes | Total quantity of all items |
| `points` | integer | Yes | Loyalty points earned |

### Example Request

```json
{
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
        "price": "Rp 90.000",
        "note": "Pedas sedang, tanpa terasi"
      },
      {
        "prefix": "2.",
        "name": "Es Teh Manis",
        "qty": 2,
        "price": "Rp 10.000"
      }
    ],
    "total": "Rp 100.000",
    "tax": "Rp 10.000",
    "cash": "Rp 150.000",
    "change": "Rp 40.000",
    "total_items": 2,
    "total_qty": 4,
    "points": 100
  }
}
```

---

## 4. CloseBill Template (`closebill.txt`)

### Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `store_name` | string | Yes | Restaurant/store name |
| `address_line_1` | string | Yes | First line of address |
| `address_line_2` | string | No | Second line of address |
| `city_line` | string | Yes | City and postal code |
| `npwp` | string | Yes | Tax ID number (NPWP) |
| `phone` | string | Yes | Contact phone number |
| `email` | string | Yes | Contact email |
| `date` | string | Yes | Transaction date (YYYY-MM-DD) |
| `time` | string | Yes | Transaction time (HH:MM:SS) |
| `bill_no` | string | Yes | Bill number |
| `table_no` | string | Yes | Table number |
| `cashier_label` | string | Yes | Cashier name (e.g., "Kasir: Alice") |
| `items` | array | Yes | Array of purchased items |
| `items[].prefix` | string | Yes | Item number prefix (e.g., "1.") |
| `items[].name` | string | Yes | Item name (will be displayed in bold) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].price` | string | Yes | Item total price (formatted) |
| `items[].note` | string | No | Special notes for this item |
| `subtotal` | string | Yes | Subtotal before tax (formatted with Rp) |
| `tax` | string | Yes | Tax amount (formatted with Rp) |
| `discount` | string | No | Discount amount (formatted with Rp) |
| `total` | string | Yes | Grand total (formatted with Rp) |
| `payments` | array | Yes | Array of payment methods used |
| `payments[].type` | string | Yes | Payment type (e.g., "Cash", "Card", "E-Wallet") |
| `payments[].amount` | string | Yes | Amount paid via this method (formatted with Rp) |
| `total_payment` | string | Yes | Total amount paid (formatted with Rp) |
| `change` | string | Yes | Change returned (formatted with Rp) |
| `total_items` | integer | Yes | Total number of item types |
| `total_qty` | integer | Yes | Total quantity of all items |
| `tagline` | string | No | Store tagline/closing message |

### Example Request

```json
{
  "template_name": "closebill.txt",
  "printer_code": "BAR",
  "metadata": {
    "store_name": "ANEKA Restoran",
    "address_line_1": "Jl. Sudirman No. 123",
    "address_line_2": "Kelurahan Senayan",
    "city_line": "Jakarta Selatan, DKI Jakarta 12190",
    "npwp": "01.234.567.8-901.000",
    "phone": "+62 21 5551234",
    "email": "info@anekarestoran.com",
    "date": "2026-02-21",
    "time": "20:15:30",
    "bill_no": "BILL-2026-0221-0089",
    "table_no": "12",
    "cashier_label": "Kasir: Siti",
    "items": [
      {
        "prefix": "1.",
        "name": "Nasi Goreng Special",
        "qty": 2,
        "price": "Rp 90.000",
        "note": "Pedas sedang, tanpa terasi"
      },
      {
        "prefix": "2.",
        "name": "Es Teh Manis",
        "qty": 3,
        "price": "Rp 15.000"
      }
    ],
    "subtotal": "Rp 105.000",
    "tax": "Rp 10.500",
    "discount": "Rp 5.000",
    "total": "Rp 110.500",
    "payments": [
      {"type": "Cash", "amount": "Rp 60.500"},
      {"type": "Card (Visa)", "amount": "Rp 50.000"}
    ],
    "total_payment": "Rp 110.500",
    "change": "Rp 0",
    "total_items": 2,
    "total_qty": 5,
    "tagline": "Terima Kasih"
  }
}
```

---

## 5. Invoice Template (`invoice.txt`)

### Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `store_name` | string | Yes | Business name |
| `address_line_1` | string | Yes | First line of business address |
| `address_line_2` | string | No | Second line of business address |
| `city_line` | string | Yes | City and postal code |
| `npwp` | string | Yes | Tax ID number (NPWP) |
| `phone` | string | Yes | Contact phone number |
| `email` | string | Yes | Contact email |
| `website` | string | No | Company website |
| `invoice_no` | string | Yes | Invoice number |
| `date` | string | Yes | Invoice date (YYYY-MM-DD) |
| `time` | string | Yes | Invoice time (HH:MM:SS) |
| `due_date` | string | No | Payment due date (YYYY-MM-DD) |
| `customer_name` | string | Yes | Customer/company name |
| `customer_address` | string | No | Customer address |
| `customer_phone` | string | No | Customer phone number |
| `items` | array | Yes | Array of invoice line items |
| `items[].no` | string | Yes | Item sequence number |
| `items[].name` | string | Yes | Item/service description (will be displayed in bold) |
| `items[].qty` | integer | Yes | Quantity |
| `items[].unit_price` | string | Yes | Price per unit (formatted with Rp) |
| `items[].discount` | string | No | Discount per item (formatted with Rp) |
| `items[].note` | string | No | Special notes for this item |
| `items[].amount` | string | Yes | Line total (formatted with Rp) |
| `subtotal` | string | Yes | Subtotal before tax (formatted with Rp) |
| `discount` | string | No | Total discount (formatted with Rp) |
| `tax_rate` | string | No | Tax percentage (e.g., "11") |
| `tax` | string | Yes | Tax amount (formatted with Rp) |
| `service_charge` | string | No | Service charge (formatted with Rp) |
| `total` | string | Yes | Grand total (formatted with Rp) |
| `payment_status` | string | No | Payment status (e.g., "PAID", "UNPAID", "PARTIAL") |
| `payment_method` | string | No | Payment method used |
| `notes` | string | No | Additional notes/terms |
| `tagline` | string | No | Company tagline/slogan |

### Example Request

```json
{
  "template_name": "invoice.txt",
  "printer_code": "RECEIPT",
  "metadata": {
    "store_name": "ANEKA Catering Services",
    "address_line_1": "Jl. Gatot Subroto No. 88",
    "address_line_2": "Kuningan",
    "city_line": "Jakarta Selatan 12950",
    "npwp": "03.456.789.0-123.000",
    "phone": "+62 21 5558888",
    "email": "invoice@anekacatering.com",
    "website": "www.anekacatering.com",
    "invoice_no": "INV-2026-0221-0456",
    "date": "2026-02-21",
    "time": "10:00:00",
    "due_date": "2026-03-07",
    "customer_name": "PT. Maju Bersama",
    "customer_address": "Jl. Thamrin No. 45, Jakarta",
    "customer_phone": "+62 21 3334444",
    "items": [
      {
        "no": "1",
        "name": "Paket Nasi Box (50 pax)",
        "qty": 50,
        "unit_price": "Rp 35.000",
        "amount": "Rp 1.750.000",
        "note": "Termasuk nasi putih, ayam goreng, sayur"
      },
      {
        "no": "2",
        "name": "Snack Box (50 pax)",
        "qty": 50,
        "unit_price": "Rp 25.000",
        "amount": "Rp 1.250.000"
      }
    ],
    "subtotal": "Rp 3.000.000",
    "tax_rate": "11",
    "tax": "Rp 330.000",
    "service_charge": "Rp 150.000",
    "total": "Rp 3.480.000",
    "payment_status": "UNPAID",
    "payment_method": "Bank Transfer",
    "notes": "Pembayaran melalui transfer bank\nBank BCA No: 1234567890\na.n. PT Aneka Catering",
    "tagline": "Quality Catering Services"
  }
}
```

---

## 6. Bar Template (`bar.txt`)

### Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_no` | string | Yes | Order number/ID |
| `table_no` | string | Yes | Table number or location |
| `server_name` | string | No | Server/waiter name (default: "Bar") |
| `time` | string | Yes | Order time (HH:MM:SS) |
| `items` | array | Yes | Array of drink items |
| `items[].qty` | integer | Yes | Quantity of drinks |
| `items[].name` | string | Yes | Drink/beverage name (will be displayed in bold) |
| `items[].note` | string | No | Special preparation notes (e.g., "Extra lime", "No ice") |
| `total_qty` | integer | Yes | Total quantity of all drinks |
| `special_note` | string | No | Special instructions or priority notes |
| `time_ordered` | string | No | Short time format for display (HH:MM) |

### Example Request

```json
{
  "template_name": "bar.txt",
  "printer_code": "BAR",
  "metadata": {
    "order_no": "BAR-002",
    "table_no": "7",
    "server_name": "Bob",
    "time": "21:30:00",
    "items": [
      {
        "qty": 1,
        "name": "Long Island Ice Tea",
        "note": "Extra lime"
      },
      {
        "qty": 2,
        "name": "Whiskey Sour",
        "note": "No ice"
      },
      {
        "qty": 1,
        "name": "Cosmopolitan"
      }
    ],
    "total_qty": 4,
    "special_note": "VIP Table - Priority Service",
    "time_ordered": "21:30"
  }
}
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "Print job sent to printer.",
  "job_id": "uuid-string",
  "html_preview": null,
  "printer_id": "uuid-string"
}
```

### Preview Response (No Printer Specified)

```json
{
  "success": true,
  "message": "Rendered successfully; no printer specified.",
  "job_id": "uuid-string",
  "html_preview": "rendered template content...",
  "printer_id": null
}
```

### Error Response

```json
{
  "success": false,
  "message": "Error description",
  "job_id": "uuid-string",
  "html_preview": "rendered content (if applicable)",
  "printer_id": null
}
```

---

## Notes

- **Rupiah Formatting**: All price fields should be pre-formatted as strings with "Rp" prefix and thousand separators (e.g., "Rp 1.250.000")
- **Dates**: Use ISO format (YYYY-MM-DD) for dates
- **Times**: Use 24-hour format (HH:MM:SS) for times
- **Printer Selection**: Use either `printer_code` (configured in YAML) or `printer_id` (from API). If both omitted, returns preview only
- **Template Extensions**: Always include `.txt` extension in `template_name` (e.g., "receipt.txt", not "receipt")
- **Line Width**: All templates are designed for 40-column thermal printers
