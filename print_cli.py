#!/usr/bin/env python3
"""
Printer API CLI Tool
Command-line interface for sending print jobs to the Printer API
"""

import argparse
import json
import sys
from datetime import datetime
import requests


API_BASE_URL = "http://localhost:9191/api/v1"


def format_rupiah(amount):
    """Format number as Rupiah (e.g., 15000 -> 'Rp 15.000')"""
    return f"Rp {amount:,.0f}".replace(",", ".")


def print_receipt(args):
    """Print a receipt to the specified printer"""
    
    # Sample items if not provided
    items = [
        {
            "prefix": "1.",
            "name": "Nasi Goreng Special",
            "qty": 2,
            "price": format_rupiah(45000)
        },
        {
            "prefix": "2.",
            "name": "Es Teh Manis",
            "qty": 2,
            "price": format_rupiah(10000)
        },
        {
            "prefix": "3.",
            "name": "Sate Ayam (10 tusuk)",
            "qty": 1,
            "price": format_rupiah(35000)
        }
    ]
    
    subtotal = 100000
    tax = 10000
    total = subtotal + tax
    
    now = datetime.now()
    
    payload = {
        "template_name": "receipt.txt",
        "printer_code": args.printer or "BAR",
        "metadata": {
            "store_name": args.store_name or "ANEKA Restoran",
            "address_line_1": "Jl. Sudirman No. 123",
            "address_line_2": "Kelurahan Senayan",
            "city_line": "Jakarta Selatan, DKI Jakarta 12190",
            "npwp": "01.234.567.8-901.000",
            "phone": "+62 21 5551234",
            "email": "info@anekarestoran.com",
            "tagline": "Authentic Indonesian Cuisine",
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "invoice_no": f"INV-{now.strftime('%Y%m%d-%H%M%S')}",
            "cashier_label": f"Cashier: {args.cashier or 'System'}",
            "items": items,
            "total": format_rupiah(total),
            "tax": format_rupiah(tax),
            "cash": format_rupiah(150000),
            "change": format_rupiah(150000 - total),
            "total_items": len(items),
            "total_qty": sum(item["qty"] for item in items),
            "points": int(total / 1000)
        }
    }
    
    if args.no_printer:
        del payload["printer_code"]
    
    return send_print_job(payload)


def print_kitchen(args):
    """Print a kitchen order to the specified printer"""
    
    items = [
        {"name": "Nasi Goreng Special", "qty": 2},
        {"name": "Sate Ayam", "qty": 1},
        {"name": "Es Teh Manis", "qty": 2}
    ]
    
    payload = {
        "template_name": "kitchen.txt",
        "printer_code": args.printer or "KITCHEN",
        "metadata": {
            "order_no": args.order_no or f"ORD-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "table_no": args.table or "7",
            "customer_name": args.customer or "Guest",
            "items": items,
            "kitchen_note": args.note or "No special requests"
        }
    }
    
    if args.no_printer:
        del payload["printer_code"]
    
    return send_print_job(payload)


def send_print_job(payload):
    """Send print job to API"""
    url = f"{API_BASE_URL}/initiate-print"
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success"):
            print(f"✓ Print job sent successfully!")
            print(f"  Job ID: {result.get('job_id')}")
            if result.get("printer_id"):
                print(f"  Printer ID: {result.get('printer_id')}")
            print(f"  Message: {result.get('message')}")
            
            if result.get("html_preview"):
                print("\n--- Preview ---")
                print(result.get("html_preview"))
                print("--- End Preview ---")
        else:
            print(f"✗ Print job failed: {result.get('message')}")
            return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to API: {e}")
        return False


def list_printers(args):
    """List all registered printers"""
    url = f"{API_BASE_URL}/printers"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        printers = response.json()
        
        if not printers:
            print("No printers registered.")
            return True
        
        print(f"\n{'ID':<38} {'Code':<12} {'Name':<20} {'Host':<15} {'Port':<6} {'Status'}")
        print("-" * 110)
        
        for p in printers:
            status = "✓" if p.get("is_available") else "✗"
            code = p.get("printer_code") or "-"
            print(f"{p['id']:<38} {code:<12} {p['name']:<20} {p['host']:<15} {p['port']:<6} {status}")
        
        print(f"\nTotal: {len(printers)} printer(s)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to API: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Printer API CLI Tool - Send print jobs to thermal printers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Print receipt to BAR printer
  %(prog)s receipt --printer BAR

  # Print kitchen order
  %(prog)s kitchen --printer KITCHEN --table 5 --customer "John Doe"

  # Preview receipt without printing
  %(prog)s receipt --no-printer

  # List all printers
  %(prog)s list
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Receipt command
    receipt_parser = subparsers.add_parser("receipt", help="Print a receipt")
    receipt_parser.add_argument("--printer", "-p", help="Printer code (e.g., BAR, KITCHEN)")
    receipt_parser.add_argument("--store-name", "-s", help="Store name")
    receipt_parser.add_argument("--cashier", "-c", help="Cashier name")
    receipt_parser.add_argument("--no-printer", action="store_true", help="Preview only, don't send to printer")
    
    # Kitchen command
    kitchen_parser = subparsers.add_parser("kitchen", help="Print a kitchen order")
    kitchen_parser.add_argument("--printer", "-p", help="Printer code (e.g., KITCHEN)")
    kitchen_parser.add_argument("--order-no", "-o", help="Order number")
    kitchen_parser.add_argument("--table", "-t", help="Table number")
    kitchen_parser.add_argument("--customer", "-c", help="Customer name")
    kitchen_parser.add_argument("--note", "-n", help="Kitchen note")
    kitchen_parser.add_argument("--no-printer", action="store_true", help="Preview only, don't send to printer")
    
    # List command
    subparsers.add_parser("list", help="List all registered printers")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "receipt":
        success = print_receipt(args)
    elif args.command == "kitchen":
        success = print_kitchen(args)
    elif args.command == "list":
        success = list_printers(args)
    else:
        parser.print_help()
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
