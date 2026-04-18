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
| `cashier_name` | string | No | Cashier name printed on ticket |
| `input_by` | string | No | Username/operator who input the order |
| `items` | array | Yes | Array of order items |
| `items[].name` | string | Yes | Item name (displayed in **bold + double-height**) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].note` | string | No | Special notes for this item |
| `kitchen_note` | string | No | Special instructions for kitchen |
| `cancel_order` | integer | No | Set to `1` to print bold **CANCELLATION** banner |
| `reprint_count` | integer | No | Reprint sequence number; when > 0 a bold **REPRINT N** banner is printed |

### Example Request

```json
{
  "template_name": "kitchen.txt",
  "printer_code": "KITCHEN",
  "metadata": {
    "order_no": "ORD-20260221-001",
    "table_no": "7",
    "cashier_name": "Siti",
    "input_by": "system",
    "customer_name": "Budi Santoso",
    "items": [
      {"name": "Nasi Goreng Special", "qty": 2, "note": "Pedas sedang, tanpa terasi"},
      {"name": "Sate Ayam (10 tusuk)", "qty": 1},
      {"name": "Es Teh Manis", "qty": 2}
    ],
    "kitchen_note": "Nasi goreng: pedas sedang\nSate: matang sempurna",
    "reprint_count": 2
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
| `cashier_name` | string | No | Cashier name printed on ticket |
| `input_by` | string | No | Username/operator who input the order |
| `items` | array | Yes | Array of order items |
| `items[].name` | string | Yes | Item name (displayed in **bold + double-height**) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].note` | string | No | Special notes for this item |
| `checker_note` | string | No | Special instructions for checker/waiter |
| `cancel_order` | integer | No | Set to `1` to print bold **CANCELLATION** banner |
| `reprint_count` | integer | No | Reprint sequence number; when > 0 a bold **REPRINT N** banner is printed |

### Example Request

```json
{
  "template_name": "checker.txt",
  "printer_code": "CHECKER",
  "metadata": {
    "order_no": "ORD-20260221-001",
    "table_no": "7",
    "cashier_name": "Siti",
    "input_by": "system",
    "customer_name": "Budi Santoso",
    "items": [
      {"name": "Nasi Goreng Special", "qty": 2, "note": "Pedas sedang, tanpa terasi"},
      {"name": "Sate Ayam (10 tusuk)", "qty": 1},
      {"name": "Es Teh Manis", "qty": 2}
    ],
    "checker_note": "Customer allergic to peanuts",
    "reprint_count": 2
  }
}
```

---

## 2b. Table Checker Template (`table_checker.txt`)

### Contract

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `order_no` | string | Yes | Order number/ID |
| `table_no` | string | Yes | Table number |
| `pax_count` | integer | No | Number of guests |
| `customer_name` | string | Yes | Customer name |
| `cashier_name` | string | No | Cashier name printed on ticket |
| `input_by` | string | No | Username/operator who input the order |
| `items` | array | Yes | Array of order items |
| `items[].name` | string | Yes | Item name (displayed in **bold + double-size**) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].note` | string | No | Special notes for this item |
| `checker_note` | string | No | Special instructions for checker/waiter |
| `cancel_order` | integer | No | Set to `1` to print bold **CANCELLATION** banner |
| `reprint_count` | integer | No | Reprint sequence number; when > 0 a bold **REPRINT N** banner is printed |

### Example Request

```json
{
  "template_name": "table_checker.txt",
  "printer_code": "CHECKER",
  "metadata": {
    "order_no": "ORD-20260221-001",
    "table_no": "7",
    "pax_count": 4,
    "cashier_name": "Siti",
    "input_by": "system",
    "customer_name": "Budi Santoso",
    "items": [
      {"name": "Nasi Goreng Special", "qty": 2, "note": "Pedas sedang"},
      {"name": "Es Teh Manis", "qty": 2}
    ],
    "checker_note": "",
    "reprint_count": 1
  }
}
```

---

## 2c. Kitchen Checker Template (`kitchen_checker.txt`)

### Contract

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `order_no` | string | Yes | Order number/ID |
| `table_no` | string | Yes | Table number |
| `customer_name` | string | Yes | Customer name |
| `items` | array | Yes | Array of order items |
| `items[].name` | string | Yes | Item name (displayed in **bold + double-size**) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].note` | string | No | Special notes for this item |
| `kitchen_note` | string | No | Special instructions for kitchen |
| `cancel_order` | integer | No | Set to `1` to print bold **CANCELLATION** banner |
| `reprint_count` | integer | No | Reprint sequence number; when > 0 a bold **REPRINT N** banner is printed |

### Example Request

```json
{
  "template_name": "kitchen_checker.txt",
  "printer_code": "KITCHEN",
  "metadata": {
    "order_no": "ORD-20260221-001",
    "table_no": "7",
    "customer_name": "Budi Santoso",
    "items": [
      {"name": "Nasi Goreng Special", "qty": 2, "note": "Pedas sedang"},
      {"name": "Sate Ayam", "qty": 1}
    ],
    "kitchen_note": "Matang sempurna",
    "reprint_count": 1
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
| `customer_name` | string | No | Customer name (printed on receipt) |
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
| `reprint_count` | integer | No | Reprint sequence number; when > 0 a bold **REPRINT N** banner is printed after the header |

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
    "reprint_count": 2,
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
| `customer_name` | string | No | Customer name (printed under table) |
| `cashier_name` | string | No | Cashier name printed on close bill |
| `input_by` | string | No | Username/operator who created the bill |
| `items` | array | Yes | Array of purchased items |
| `items[].name` | string | Yes | Item name (will be displayed in bold) |
| `items[].qty` | integer | Yes | Item quantity |
| `items[].price` | string | Yes | Item total price (formatted) |
| `items[].note` | string | No | Special notes for this item |
| `subtotal` | string | Yes | Subtotal before charges (formatted with Rp) |
| `service_charge_amount` | string | No | Service charge amount (formatted with Rp) |
| `service_charge_prct` | number | No | Service charge percentage (e.g., 5 or 5.0) |
| `reprint_count` | integer | No | Reprint sequence number; when > 0 a bold **REPRINT N** banner is printed after the header |
| `tax` | string | Yes | Tax amount / PB1 (formatted with Rp) |
| `discount` | string | No | Discount amount (formatted with Rp) |
| `discount_prct` | number | No | Discount percentage (e.g., 10 or 10.0) |
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
    "customer_name": "Budi Santoso",
    "cashier_name": "Siti",
    "input_by": "system",
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
    "service_charge_amount": "Rp 5.250",
    "service_charge_prct": 5,
    "tax": "Rp 10.500",
    "discount": "Rp 5.000",
    "discount_prct": 10,
    "total": "Rp 115.750",
    "payments": [
      {"type": "Cash", "amount": "Rp 60.500"},
      {"type": "Card (Visa)", "amount": "Rp 50.000"}
    ],
    "total_payment": "Rp 110.500",
    "change": "Rp 0",
    "total_items": 2,
    "total_qty": 5,
    "tagline": "Terima Kasih",
    "reprint_count": 2
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
| `cashier_name` | string | No | Cashier name printed on invoice |
| `input_by` | string | No | Username/operator who created the invoice |
| `items` | array | Yes | Array of invoice line items |
| `items[].no` | string | Yes | Item sequence number |
| `items[].name` | string | Yes | Item/service description (will be displayed in bold) |
| `items[].qty` | integer | Yes | Quantity |
| `items[].unit_price` | string | Yes | Price per unit (formatted with Rp) |
| `items[].discount` | string | No | Discount per item (formatted with Rp) |
| `items[].note` | string | No | Special notes for this item |
| `items[].amount` | string | Yes | Line total (formatted with Rp) |
| `subtotal` | string | Yes | Subtotal before Tax (formatted with Rp) |
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
    "cashier_name": "Siti",
    "input_by": "system",
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

    ## 7. Close Cashier Template (`close_cashier.txt`)

    Daily cashier closing summary for 40-column thermal printers.

    ### Contract

    | Field | Type | Required | Description |
    |-------|------|----------|-------------|
    | `cashier_name` | string | Yes | Name of the closing cashier ("Closing Kasir") |
    | `cashier_no` | string | Yes | Cashier/session number ("No. Kasir") |
    | `close_date` | string | Yes | Closing date (DD-MM-YYYY) |
    | `close_time` | string | Yes | Closing time (HH:MM:SS) |
    | `sales_total` | string | Yes | Total sales amount (formatted with Rp) |
    | `total_dp` | string | No | Total DP amount (formatted with Rp) |
    | `grand_total` | string | No | Grand total amount (formatted with Rp); if omitted, `sales_total` is reused |
    | `tunai` | string | Yes | Cash payments total (formatted with Rp) |
    | `credit` | string | Yes | Credit card payments total (formatted with Rp) |
    | `debit` | string | Yes | Debit card payments total (formatted with Rp) |
    | `qris` | string | Yes | QRIS / e-wallet payments total (formatted with Rp) |
    | `opening_balance` | string | Yes | Opening cash drawer balance ("Modal POS") |
    | `change` | string | Yes | Cash taken out/withdrawn ("Penarikan Tunai") |
    | `closing_balance` | string | Yes | Final cash drawer balance ("Saldo Akhir") |
    | `printby` | string | Yes | Name printed in footer ("Print By ...") |
    | `timestamp` | string | No | Printed footer timestamp; if omitted, auto-generated in UTC+7 |

    ### Example Request

    ```json
    {
      "template_name": "close_cashier.txt",
      "printer_code": "BAR",
      "metadata": {
        "cashier_name": "HANA",
        "cashier_no": "S5K202603060001",
        "close_date": "06-03-2026",
        "close_time": "16:46:03",
        "sales_total": "Rp 16.590.450",
        "total_dp": "Rp 0",
        "grand_total": "Rp 16.590.450",
        "tunai": "Rp 5.640.950",
        "credit": "Rp 0",
        "debit": "Rp 10.949.500",
        "qris": "Rp 0",
        "opening_balance": "Rp 630.000",
        "change": "Rp 0",
        "closing_balance": "Rp 5.640.950",
        "printby": "HANA"
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
| `items[].name` | string | Yes | Drink/beverage name (displayed in **bold + double-height**, centered) |
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
- **Line Width**: 
  - Kitchen, Checker, Receipt, CloseBill, Invoice: 40 columns
  - Bar: 48 columns (wider format)
- **Text Formatting**:
  - Item names are displayed in **bold** text
  - Kitchen, Checker, and Bar templates use **double-height** text for item names (2x taller)
  - Receipt, CloseBill, and Invoice use normal-height bold text
- **Item Notes**: All templates support optional `note` field at item level for special instructions
- **Template Count**: 6 templates available (Kitchen, Checker, Receipt, CloseBill, Invoice, Bar)
