# Printer API

FastAPI service to connect to **thermal printers** on the local network for restaurant use. Prints using **HTML** templates (80mm width) rendered with **Jinja2**.

## Features

- **Printer discovery**: Scan the local network for devices with the printer port open (e.g. 9100).
- **Printer registry**: Register printers by host and port, then target them by ID.
- **Print command**: `POST /api/v1/initiate-print` with `template_name` and `metadata`; Jinja2 fills the template, the HTML is converted to **ESC/POS**, and the bytes are sent to the thermal printer.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0
```

API docs: **http://localhost:8000/docs**

## API Overview

### 1. Printer discovery

- **GET /api/v1/printers** – List registered printers.
- **GET /api/v1/printers/discover?network=192.168.1&port=9100** – Scan network for devices with the given port open.
- **POST /api/v1/printers** – Register a printer (body: `name`, `host`, `port`).
- **GET /api/v1/printers/{printer_id}** – Get printer details.
- **DELETE /api/v1/printers/{printer_id}** – Remove a printer.

### 2. Print command

**POST /api/v1/initiate-print**

```json
{
  "template_name": "receipt",
  "metadata": {
    "restaurant_name": "My Restaurant",
    "order_id": "1234",
    "table_name": "5",
    "items": [
      { "name": "Burger", "quantity": 1, "price": 12.99 },
      { "name": "Fries", "quantity": 2, "price": 3.50 }
    ],
    "subtotal": 19.99,
    "tax": 1.60,
    "total": 21.59,
    "thank_you_message": "Thank you!"
  },
  "printer_id": "optional-uuid-of-registered-printer"
}
```

- **template_name**: Jinja2 template file name without `.html` (e.g. `receipt` → `app/templates/receipt.html`).
- **metadata**: Any object; keys are passed as variables into the template.
- **printer_id**: Optional. If provided, the rendered HTML is converted to ESC/POS and sent to that printer. If omitted, the response includes `html_preview` for debugging.

## Templates

Templates live in **`app/templates/`** as `.html` files. They are standard Jinja2; use `metadata` keys as variables (e.g. `{{ restaurant_name }}`, `{% for item in items %}`).

### Default: `receipt.html` (80mm)

Variables you can pass in `metadata`:

| Variable           | Description                |
|--------------------|----------------------------|
| `restaurant_name`  | Header title               |
| `tagline`          | Subtitle                   |
| `order_id`         | Order number               |
| `table_name`       | Table                      |
| `date`             | Date/time                  |
| `server`           | Server name                |
| `items`            | List of `{ name, quantity?, price?, notes? }` |
| `subtotal`         | Subtotal                   |
| `tax`              | Tax                        |
| `discount`         | Discount                   |
| `total`            | Total                      |
| `thank_you_message`| Footer text                |

### Kitchen: `kitchen.html` (80mm)

Kitchen order ticket with only order and table info (no prices). Variables in `metadata`:

| Variable        | Description                                      |
|-----------------|--------------------------------------------------|
| `customer_name` | Customer name                                    |
| `table_no`      | Table number                                     |
| `order_id`      | Order ID                                         |
| `items`         | List of `{ order_name, order_qty }` (or `name`, `qty`) |

**Example request:**

```json
{
  "template_name": "kitchen",
  "metadata": {
    "customer_name": "John",
    "table_no": "5",
    "order_id": "1234",
    "items": [
      { "order_name": "Burger", "order_qty": 1 },
      { "order_name": "Fries", "order_qty": 2 }
    ]
  },
  "printer_id": "<printer-uuid>"
}
```

## ESC/POS conversion

The app converts **HTML to ESC/POS** before sending to the printer. The converter supports:

- **Text**: plain text, line breaks, paragraphs
- **Formatting**: **bold** (`<b>`, `<strong>`), double-size headings (`<h1>`–`<h3>`)
- **Alignment**: center (e.g. elements with class `header`, `footer`, `totals`)
- **Tables**: simple rows and cells (flattened to lines)
- **Paper**: feed and full cut at the end

So you keep writing HTML/Jinja2 templates; the thermal printer receives standard ESC/POS commands over TCP (port **9100**). No extra print server or driver is required.

## Configuration

Environment variables (optional):

- `PRINTER_TEMPLATES_DIR` – Override templates directory.
- `PRINTER_DISCOVERY_TIMEOUT_SECONDS` – Timeout per host during discovery (default: 1.0).
