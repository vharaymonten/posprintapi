# POS Printer Guide

How this service talks to thermal POS printers: the wire protocol, how printers are
configured, and how to diagnose failures.

Related: [API_CONTRACTS.md](../API_CONTRACTS.md) for request payloads per template,
[CORS_CONFIG.md](../CORS_CONFIG.md) for CORS.

**Contents**

- [Protocol](#protocol) — raw TCP on port 9100, ESC/POS commands, images, retries
  - [Transport: raw TCP, one-way](#transport-raw-tcp-one-way)
  - [Anatomy of a print job](#anatomy-of-a-print-job)
  - [ESC/POS command set in use](#escpos-command-set-in-use)
  - [Text encoding and layout](#text-encoding-and-layout)
  - [Images](#images)
  - [Retry behaviour](#retry-behaviour)
  - [Status queries (not implemented)](#status-queries-not-implemented)
- [Setup](#setup) — `printers.yaml`, SQLite registry, discovery, settings, Docker
  - [Where printer definitions live](#where-printer-definitions-live)
  - [Addressing a printer in a print request](#addressing-a-printer-in-a-print-request)
  - [Availability checks](#availability-checks)
  - [Network discovery](#network-discovery)
  - [Management API](#management-api)
  - [Settings](#settings)
  - [Docker](#docker)
  - [Templates](#templates)
- [Troubleshooting](#troubleshooting) — the JSON failure log, error codes, silent failures
  - [Start here: the failure log](#start-here-the-failure-log)
  - [Interpreting `error_class`](#interpreting-error_class)
  - [Silent failures: what this log *cannot* catch](#silent-failures-what-this-log-cannot-catch)
  - [Symptom to cause](#symptom-to-cause)
  - [Reproducing a failure safely](#reproducing-a-failure-safely)
  - [Replaying a lost job](#replaying-a-lost-job)

---

## Protocol

### Transport: raw TCP, one-way

There is no printer driver, no CUPS, no vendor SDK. The service opens a plain TCP socket
to the printer and writes ESC/POS bytes directly.

```
app/services/print_service.py  ->  send_to_printer()

  socket(AF_INET, SOCK_STREAM)
  settimeout(10)
  connect((printer.host, printer.port))   # port 9100 by default
  sendall(buffer)
  close                                    # via `with`
```

Port **9100** is the de-facto standard "raw"/JetDirect printing port. Nearly every
network thermal printer and every Ethernet print-server dongle listens on it.

**The channel is one-way.** The printer sends nothing back. A successful `sendall()`
proves only that the bytes reached the printer's TCP receive buffer — not that paper
moved. This is the single most important fact about this integration; see
[Status queries](#status-queries-not-implemented) below.

---

### Anatomy of a print job

`send_to_printer` wraps the rendered template body in a fixed preamble and postamble:

```python
buffer = INIT + LEFT + content + b"\n\n\n" + CUT
```

| Segment | Bytes | Purpose |
|---|---|---|
| `INIT` | `1B 40` (`ESC @`) | Reset printer to power-on defaults; clears any leftover style state from a previous job |
| `LEFT` | `1B 61 00` (`ESC a 0`) | Force left alignment as the baseline |
| `content` | UTF-8 text + inline ESC/POS + raster images | The rendered template |
| `\n\n\n` | `0A 0A 0A` | Feed three lines so the cut falls below the last text |
| `CUT` | `1D 56 00` (`GS V 0`) | Full cut |

The trailing feed matters: the cutter sits a couple of centimetres above the print head,
so cutting immediately after the last line would slice through it.

---

### ESC/POS command set in use

Defined at the top of `app/services/print_service.py`:

| Constant | Bytes | Effect |
|---|---|---|
| `INIT` | `ESC @` | Initialise / reset |
| `CENTER` | `ESC a 1` | Centre alignment |
| `LEFT` | `ESC a 0` | Left alignment |
| `BOLD_ON` | `ESC E 1` | Emphasised on |
| `BOLD_OFF` | `ESC E 0` | Emphasised off |
| `DOUBLE_HEIGHT_ON` | `ESC ! 0x10` | Double height |
| `DOUBLE_WIDTH_ON` | `ESC ! 0x20` | Double width |
| `DOUBLE_SIZE_ON` | `ESC ! 0x30` | Double height + width |
| `NORMAL_SIZE` | `ESC ! 0x00` | Reset character size |
| `CUT` | `GS V 0` | Full cut |

#### Using them from a template

Every constant is injected into the Jinja2 render context by `render_template`, decoded as
`latin-1` so each byte survives the round-trip through the string layer:

```jinja
{{ CENTER }}{{ DOUBLE_SIZE_ON }}TABLE 7{{ NORMAL_SIZE }}
{{ LEFT }}{{ BOLD_ON }}Nasi Goreng{{ BOLD_OFF }}
```

Style commands are **sticky** — the printer stays bold until you send `BOLD_OFF`. Always
close what you open, or the rest of the receipt inherits it.

Do **not** emit `CUT` from inside a template; `send_to_printer` appends it. A template-level
cut produces a second, blank slip.

---

### Text encoding and layout

- The rendered string is encoded **UTF-8 with `errors="ignore"`**
  (`_rendered_to_bytes`). Characters the printer's codepage can't represent are silently
  dropped rather than raising — stick to ASCII plus the printer's supported range.
- Templates are laid out for a **40-column** line. The `rjust` / `ljust` / `truncate`
  Jinja filters registered in `PrintService.__init__` exist for column alignment:

  ```jinja
  {{ item.name|ljust(28) }}{{ item.price|rjust(12) }}
  ```

- Auto-injected context values (UTC+7, added by `render_template` when absent):
  `date` (`YYYY-MM-DD`), `time` (`HH:MM:SS`), `timestamp` (`DD-MM-YYYY hh:mm AM/PM`).

---

### Images

Logos are not sent as files — they are rasterised into ESC/POS bitmap commands.

#### Template API

```jinja
{{ IMAGE("logo/brand.png", height_cm=2.0, align="center") }}
{{ IMAGE("logo/brand.png", height_cm=1.5, text="Thank you!") }}

{{ IMAGE_ROW([
     {"path": "logo/ig.png",  "text": "@ourshop"},
     {"path": "logo/wa.png",  "text": "0812-3456"}
   ], height_cm=0.5, gap_cm=0.4) }}
```

`IMAGE` places one logo (optionally with text beside it) on its own band. `IMAGE_ROW`
composes several logo+text pairs onto a **single** horizontal band so they print side by
side on one line — separate `IMAGE` calls would each occupy their own line.

Paths are resolved relative to the repository root.

#### How it works

1. `IMAGE` / `IMAGE_ROW` are Jinja globals that emit a placeholder token —
   `[[[IMG:<base64-json>]]]` — into the rendered text. They do no image work at render time.
2. `_rendered_to_bytes` scans the rendered string for those tokens, decodes the payload, and
   replaces each with real raster bytes, splicing the surrounding text through unchanged.
3. `_load_logo_gray` opens the file, flattens transparency onto white (a transparent PNG
   would otherwise dither to black), converts to greyscale, and scales to the requested
   height. `height_cm` → pixels at **203 dpi**.
4. `_compose_logo_text` optionally pastes text to the right of the logo, vertically centred,
   drawn with a stroke to simulate bold weight so it survives downscaling.
5. `_raster_band_bytes` clamps the band to **384 dots** (58 mm head at 203 dpi), applies
   Floyd–Steinberg dithering to 1-bit, pads the width to a byte boundary, packs the pixels
   MSB-first, and emits:

   ```
   <align>  GS v 0  m=0  xL xH  yL yH  <raster data>  \n  ESC a 0
   ```

   `GS v 0` is "print raster bit image". `xL/xH` is the row width **in bytes**, `yL/yH` the
   height in dots. Alignment is restored to left afterwards.

> **58 mm assumption.** `max_width_dots = 384` is hardcoded in `_raster_band_bytes`. On an
> 80 mm printer (576 dots) images print narrower than they could. Change that constant if
> you move to 80 mm hardware.

---

### Retry behaviour

`send_to_printer` retries once on failure:

```python
PRINT_MAX_ATTEMPTS = 2          # initial attempt + one retry
PRINT_RETRY_DELAY_SECONDS = 1.0
```

Each attempt opens a **fresh** socket — a half-dead connection is never reused. With the
10-second socket timeout, a fully unreachable printer costs about 21 seconds
(10s + 1s + 10s) before the caller sees HTTP 500. Every failed attempt is written to the
JSON failure log; see [Troubleshooting](#troubleshooting).

Retries are indiscriminate — connection refused, timeout, and mid-send errors are all
retried identically. A `sendall` that fails partway after bytes already reached the printer
could in principle produce a duplicate slip on retry, though this is rare over LAN.

---

### Status queries (not implemented)

Port 9100 is technically bidirectional, and ESC/POS defines real-time status commands. This
service does not use them, which is why out-of-paper and cover-open conditions currently
print as `[SUCCESS]`.

If you add status checking, these are the relevant commands (Epson standard — verify against
your printer's manual, vendor bit meanings vary). Send the bytes, then `recv(1)` and decode
the flags:

| Query | Bytes | Response bits |
|---|---|---|
| Printer status | `10 04 01` | bit 3 set = offline |
| Offline cause | `10 04 02` | bit 2 = cover open, bit 5 = paper end, bit 6 = error |
| Error status | `10 04 03` | bit 3 = cutter error, bit 5 = unrecoverable, bit 6 = auto-recoverable |
| Paper sensor | `10 04 04` | bits 2–3 = paper near end, bits 5–6 = paper out |

Not every low-cost clone implements `DLE EOT` correctly, so any implementation needs a short
`recv` timeout and a "no response = assume OK, proceed" fallback — otherwise working
printers would start failing.

---

## Setup

### Where printer definitions live

There are two layers, and the distinction matters when a change doesn't seem to take effect.

| Layer | File | Role |
|---|---|---|
| **YAML** | `printers.yaml` | Human-edited seed list, committed to the repo |
| **SQLite** | `printers.sqlite3` | Runtime source of truth, mutable via the API |

`printers.yaml`:

```yaml
printers:
  - name: "BAR"
    printer_code: "BAR"
    host: "192.168.3.162"
    port: 9100
```

`name` and `host` are required; entries missing either are skipped silently. `port` defaults
to `settings.default_printer_port` (9100). `printer_code` is optional but strongly
recommended — it's the stable handle print requests use.

#### Seeding rules (read this before editing the YAML)

`PrinterService.__init__` calls `seed_from_yaml(only_if_empty=True)` at startup. That flag is
the catch:

> **If the `printers` table already has any rows, the YAML is not read at all.**

So editing `printers.yaml` on an existing deployment does nothing until you either call
`seed_from_yaml()` without the flag, delete the SQLite DB, or make the change through the
API instead.

When seeding does run:

- Entries **with** a `printer_code` go through `upsert_printer_by_code` — matched on code, so
  re-seeding updates the existing row and preserves its `id`.
- Entries **without** a `printer_code` are always `INSERT`ed with a fresh UUID — re-seeding
  creates duplicates.

`printer_code` is `UNIQUE` in the schema; two YAML entries sharing a code collapse into one
row. Note that `name` is *not* unique — the current `printers.yaml` deliberately has four
entries named `"Cashier Printer"` distinguished only by their codes.

#### Schema

```sql
CREATE TABLE printers (
    id           TEXT PRIMARY KEY,   -- UUID
    name         TEXT NOT NULL,
    printer_code TEXT UNIQUE,
    host         TEXT NOT NULL,
    port         INTEGER NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
```

`is_available` is **not** stored — it's computed live on every read by `check_reachable`.

---

### Addressing a printer in a print request

`POST /api/v1/initiate-print` accepts either identifier:

```json
{ "template_name": "bar.txt", "printer_code": "BAR", "metadata": { } }
{ "template_name": "bar.txt", "printer_id":   "d8332aa4-…", "metadata": { } }
```

- **`printer_code` wins** when both are supplied.
- **Omit both** and the job renders but is not sent — the response returns the rendered text
  in `html_preview` for debugging. Nothing is logged as a failure.
- An unknown code or id is an input error, not a print failure.

Prefer `printer_code`. It's readable, stable across database rebuilds, and survives the
re-seeding rules above; UUIDs do not.

---

### Availability checks

`check_reachable(host, port)` opens a TCP connection with a **1-second** timeout
(`settings.discovery_timeout_seconds`) and reports whether it succeeded.

This is a liveness probe on the socket only. It confirms something is listening on port
9100 — not that the device is a printer, and not that it has paper. `get`, `get_by_code`,
and `list_all` all populate `is_available` this way; `list_all` fans the checks out across a
10-worker thread pool so listing N printers costs roughly one timeout, not N.

Note that `get_by_code` runs a reachability probe on **every print request**, adding up to
1 second before the job is even sent.

---

### Network discovery

```
GET /api/v1/printers/discover?network_prefix=192.168.3&port=9100
```

Scans `x.y.z.1` through `x.y.z.254` across the thread pool and returns hosts with the port
open, capped at 30 seconds overall. Discovery **only reports** — it does not register
anything. Feed the results into `POST /api/v1/printers` yourself.

Anything listening on 9100 shows up, including non-printers.

---

### Management API

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/v1/printers` | List all, each with live `is_available` |
| `POST` | `/api/v1/printers` | Register; 201 on success, duplicate `printer_code` → 400 |
| `GET` | `/api/v1/printers/discover` | Subnet scan (see above) |
| `GET` | `/api/v1/printers/{id}` | Fetch one |
| `PATCH` | `/api/v1/printers/{id}` | Partial update |
| `PUT` | `/api/v1/printers/{id}` | Replace |
| `DELETE` | `/api/v1/printers/{id}` | 204 on success |

Changes made here write to SQLite and take effect immediately — no restart, no YAML edit.

---

### Settings

All fields on `Settings` (`app/core/config.py`) are overridable by environment variable using
the `PRINTER_` prefix — `print_log_path` becomes `PRINTER_PRINT_LOG_PATH`.

| Setting | Default | Purpose |
|---|---|---|
| `printers_config_path` | `./printers.yaml` | Seed file location |
| `sqlite_db_path` | `./printers.sqlite3` | Runtime database |
| `default_printer_port` | `9100` | Applied when a YAML entry omits `port` |
| `discovery_timeout_seconds` | `1.0` | Reachability probe timeout |
| `templates_dir` | `app/templates` | HTML templates (legacy) |
| `print_log_path` | `./logs/print_failures.log` | Failure log |
| `print_log_max_bytes` | `5242880` | Rotate at 5 MB |
| `print_log_backup_count` | `5` | Keep 5 rotated files |
| `print_log_include_metadata` | `true` | Log the full request payload |

CORS settings are deliberately configured in code, not by env var — see
[CORS_CONFIG.md](../CORS_CONFIG.md).

---

### Docker

`docker-compose.yml` redirects the writable paths onto the `printer_data` volume:

```yaml
environment:
  PRINTER_SQLITE_DB_PATH: "/data/printers.sqlite3"
  PRINTER_PRINTERS_CONFIG_PATH: "/app/printers.yaml"
  PRINTER_PRINT_LOG_PATH: "/data/logs/print_failures.log"
volumes:
  - printer_data:/data
  - ./printers.yaml:/app/printers.yaml:ro
```

The YAML is bind-mounted read-only, so editing it on the host is picked up on the next
container start — subject to the `only_if_empty` rule above, which means an existing
`/data/printers.sqlite3` will shadow your edits.

The container must reach the printer VLAN. With the default bridge network it uses the
Docker host's routing; if printers sit on a segment the host can't reach, no amount of
configuration here will help.

---

### Templates

Plain-text ESC/POS templates live in `receipt_templates/`:

```
bar.txt      checker.txt      close_cashier.txt   closebill.txt   invoice.txt
kitchen.txt  kitchen_checker.txt   receipt.txt    table_checker.txt
```

`template_name` is resolved by `render_template` through a `ChoiceLoader` that searches
`settings.templates_dir` first, then `receipt_templates/`. **Always include the `.txt`
extension** — a name without a suffix has `.html` appended for backwards compatibility and
will not find these files.

---

## Troubleshooting

### Start here: the failure log

Every failed print job appends one JSON object per line to
`logs/print_failures.log` (`/data/logs/print_failures.log` in Docker). Rotated at 5 MB,
5 backups kept. The path is configurable via `PRINTER_PRINT_LOG_PATH`.

```bash
# everything, newest last
tail -f logs/print_failures.log | jq .

# just the delivery failures
jq -c 'select(.error_type=="printer_failure")' logs/print_failures.log

# which printers are failing, ranked
jq -r 'select(.printer) | .printer.printer_code' logs/print_failures.log | sort | uniq -c | sort -rn

# reconstruct a lost receipt — the full request payload is in the entry
jq 'select(.job_id=="b1e5280d-…") | .metadata' logs/print_failures.log
```

#### Entry format

```json
{
  "ts": "2026-08-01T14:13:50.218+07:00",
  "level": "error",
  "event": "printer_send_failed",
  "error_type": "printer_failure",
  "job_id": "b1e5280d-d0b7-4509-8a8d-d3d97f96d341",
  "template_name": "bar.txt",
  "printer": {"id": "d8332aa4-…", "printer_code": "BAR", "name": "BAR",
              "host": "192.168.3.162", "port": 9100},
  "attempt": 1, "max_attempts": 2, "final": false,
  "error": "timed out", "error_class": "TimeoutError", "traceback": "…",
  "metadata": { }
}
```

| Field | Notes |
|---|---|
| `ts` | ISO-8601, **UTC+7** (Jakarta), millisecond precision |
| `event` | Where it failed — see table below |
| `error_type` | `printer_failure` (→ HTTP 500) or `input_error` (→ HTTP 400) |
| `job_id` | Correlates the retry attempts of one job; also returned in the API response |
| `printer` | `null` when the failure happened before a printer was resolved |
| `attempt` / `final` | Delivery failures only. `final: true` marks the last attempt |
| `metadata` | The **full** original request payload — enough to replay the job |

#### Events

| `event` | `error_type` | Cause |
|---|---|---|
| `render_failed` | input_error | Template missing, or Jinja2 raised while rendering |
| `printer_not_found` | input_error | `printer_code` / `printer_id` matched no row |
| `image_build_failed` | input_error | Bad `IMAGE`/`IMAGE_ROW` token, or a logo file is missing/corrupt |
| `printer_send_failed` | printer_failure | Socket failure. **One entry per attempt** — a single failed job normally produces two |

A job with no printer specified renders a preview and logs nothing — that's a success, not a
failure.

The log is best-effort by design: if the file can't be opened (read-only filesystem, bad
path) the service prints one `[WARN]` line and keeps printing normally. Logging never breaks
a print job.

---

### Interpreting `error_class`

These are **operating-system socket errors**, not printer error codes. The printer does not
report anything back — see [Silent failures](#silent-failures-what-this-log-cannot-catch).

| `error_class` | errno | Meaning | Where to look |
|---|---|---|---|
| `ConnectionRefusedError` | 61 `ECONNREFUSED` | Host is up, nothing listening on the port | Printer powered on but network module crashed; or wrong port |
| `TimeoutError` | — | 10s socket timeout expired | Printer unplugged, wrong IP, VLAN/firewall blocking, printer asleep |
| `gaierror` | 8 `EAI_NONAME` | DNS resolution failed | Hostname in `printers.yaml` is wrong — use IPs |
| `BrokenPipeError` | 32 `EPIPE` | Connection died mid-send | Printer rebooted or dropped the link during transfer |
| `ConnectionResetError` | 54 `ECONNRESET` | Printer forcibly closed the connection | Printer busy or its TCP stack wedged |
| `OSError` "No route to host" | 65 `EHOSTUNREACH` | Network can't reach that subnet | Routing/VLAN; from Docker, check host routing |

`ConnectionRefusedError` and `TimeoutError` cover the overwhelming majority in practice.

---

### Silent failures: what this log *cannot* catch

Raw ESC/POS over port 9100 is **one-way**. `sendall()` succeeding means the bytes reached the
printer's TCP buffer — nothing more. These conditions log `[SUCCESS]`, write **nothing** to
the failure log, return HTTP 200, and produce no receipt:

- Out of paper
- Cover open
- Print head overheated
- Cutter jammed
- Printer online but in an error state
- A network print-server dongle accepting TCP on behalf of a dead printer

**If a job is missing from the failure log but no receipt appeared, the problem is at the
printer, not the network.** Go look at the device.

Closing this gap requires ESC/POS `DLE EOT` status queries before sending; the commands and
their caveats are documented in
[Status queries](#status-queries-not-implemented).

---

### Symptom to cause

#### Nothing prints, HTTP 500 after ~21 seconds

Two `printer_send_failed` entries with `TimeoutError`. That's the retry policy: 10s timeout
+ 1s delay + 10s timeout. The printer is unreachable.

```bash
# is anything listening?
nc -zv 192.168.3.162 9100
# does the API agree?
curl -s localhost:9191/api/v1/printers | jq '.[] | {printer_code, host, is_available}'
```

#### Nothing prints, HTTP 200

The silent-failure case above. Check paper, cover, and the printer's error LED.

#### HTTP 400 "Printer not found with code: X"

A `printer_not_found` entry. The code isn't in SQLite. Remember that editing
`printers.yaml` does **not** re-seed an already-populated database — see the seeding rules in
[Seeding rules](#seeding-rules-read-this-before-editing-the-yaml).
Register it through the API instead:

```bash
curl -X POST localhost:9191/api/v1/printers -H 'Content-Type: application/json' \
  -d '{"name":"BAR","printer_code":"BAR","host":"192.168.3.162","port":9100}'
```

#### HTTP 400 "Template not found"

A `render_failed` entry. Include the `.txt` extension — a bare name gets `.html` appended and
won't match anything in `receipt_templates/`.

#### HTTP 400 "Image not found"

An `image_build_failed` entry. `IMAGE()` paths resolve from the repository root. In Docker,
only `app/`, `receipt_templates/`, `logo/`, and `printers.yaml` are copied into the image — a
logo outside those directories exists locally but not in the container.

#### Receipt prints but looks wrong

Not a failure-log matter — nothing errored. Check the template:

- **Everything bold after a certain line** — a `BOLD_ON` without its `BOLD_OFF`. Style
  commands are sticky.
- **Two slips, second one blank** — the template emits its own `CUT`; `send_to_printer`
  already appends one.
- **Columns misaligned** — templates assume 40 columns; use the `ljust`/`rjust` filters.
- **Logo too narrow / clipped** — images are clamped to 384 dots for a 58 mm head. On 80 mm
  hardware, raise `max_width_dots` in `_raster_band_bytes`.
- **Missing characters** — text is encoded UTF-8 with `errors="ignore"`; unsupported
  characters vanish silently.

#### The failure log doesn't exist

It's created lazily on the first failure — an empty parent directory is normal on a healthy
system. If failures *are* happening and the file still isn't there, look for a
`[WARN] Print failure log disabled` line on stdout (`docker compose logs printer-api`):
permissions or a read-only path.

---

### Reproducing a failure safely

Point a test printer at an unroutable address and fire a job — no hardware needed:

```bash
curl -X POST localhost:9191/api/v1/printers -H 'Content-Type: application/json' \
  -d '{"name":"TEST","printer_code":"TEST_DEAD","host":"192.0.2.1","port":9100}'

curl -X POST localhost:9191/api/v1/initiate-print -H 'Content-Type: application/json' \
  -d '{"template_name":"bar.txt","printer_code":"TEST_DEAD","metadata":{"order_id":"TEST"}}'
```

Expect HTTP 500 after ~21 seconds and two `printer_send_failed` entries.

To preview a template without any printer, omit `printer_code` and `printer_id` — the
rendered text comes back in `html_preview`.

---

### Replaying a lost job

The failure log carries the complete original payload, so a lost receipt can be reprinted:

```bash
jq -r 'select(.job_id=="<job_id>") | {template_name, metadata}' logs/print_failures.log \
  > /tmp/job.json
# add the printer_code, then POST it back to /api/v1/initiate-print
```

There is no automatic retry beyond the two in-request attempts. Once a job fails, it is gone
unless replayed by hand — the log is what makes that possible.
