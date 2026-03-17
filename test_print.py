import socket
import datetime
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
PORT = 9100
TIMEOUT = 0.5
MAX_WORKERS = 50

# --- ESC/POS RAW COMMANDS ---
ESC = b'\x1b'
GS  = b'\x1d'
INIT = ESC + b'@'
CENTER = ESC + b'a\x01'
LEFT = ESC + b'a\x00'
BOLD_ON = ESC + b'E\x01'
BOLD_OFF = ESC + b'E\x00'
CUT = GS + b'V\x00'

def check_ip(ip):
    """Checks if Port 9100 is open on a specific IP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            if s.connect_ex((ip, PORT)) == 0:
                return ip
    except:
        pass
    return None

def get_subnet():
    """Detects the local subnet prefix (e.g., 192.168.1)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return ".".join(s.getsockname()[0].split(".")[:-1])
    finally:
        s.close()

def send_test_order(ip):
    """Sends a formatted raw ESC/POS order to the printer."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Building the receipt buffer
    buffer = INIT + CENTER + BOLD_ON + b"TEST KITCHEN ORDER\n" + BOLD_OFF
    buffer += f"Date: {now}\n".encode()
    buffer += b"--------------------------------\n"
    buffer += LEFT + b"1x Margherita Pizza.........$12.00\n"
    buffer += b"   * Extra Basil\n"
    buffer += b"2x Craft Cola...............$ 6.00\n"
    buffer += b"--------------------------------\n"
    buffer += BOLD_ON + b"TOTAL:                      $18.00\n" + BOLD_OFF
    buffer += b"\n\n\n" + CUT

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((ip, PORT))
            s.sendall(buffer)
            print(f"\n[!] Success: Order sent to {ip}")
    except Exception as e:
        print(f"\n[X] Error printing to {ip}: {e}")

def main():
    print("--- ESC/POS Printer Discovery Tool ---")
    prefix = get_subnet()
    print(f"Scanning subnet {prefix}.0/24...")

    ips = [f"{prefix}.{i}" for i in range(1, 255)]
    found = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(check_ip, ips)
        for res in results:
            if res:
                found.append(res)
                print(f"  > Found: {res}")

    if not found:
        print("No printers discovered. Check your connection.")
        return

    print(f"\nDiscovered {len(found)} printer(s).")
    for idx, ip in enumerate(found):
        print(f"[{idx}] {ip}")

    try:
        choice = int(input("\nSelect a printer index to test print (or 'Ctrl+C' to exit): "))
        if 0 <= choice < len(found):
            send_test_order(found[choice])
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()