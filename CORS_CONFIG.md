# CORS Configuration Guide

The Printer API includes CORS (Cross-Origin Resource Sharing) middleware to control which domains can access the API.

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Create a `.env` file in the project root:

```bash
# Allow specific origins
PRINTER_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://yourapp.com

# Allow all origins (not recommended for production)
PRINTER_CORS_ORIGINS=*
```

### Method 2: Docker Compose

Edit `docker-compose.yml`:

```yaml
services:
  printer-api:
    environment:
      PRINTER_CORS_ORIGINS: "http://localhost:3000,http://localhost:8080"
```

### Method 3: Direct Configuration

Edit `app/core/config.py`:

```python
cors_origins: List[str] = ["http://localhost:3000", "http://yourapp.com"]
```

## Default Configuration

By default, the API allows **all origins** (`*`). This is convenient for development but should be restricted in production.

## Configuration Options

All CORS settings can be configured via environment variables with the `PRINTER_` prefix:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PRINTER_CORS_ORIGINS` | string (comma-separated) | `*` | Allowed origins |
| `PRINTER_CORS_CREDENTIALS` | boolean | `true` | Allow credentials |
| `PRINTER_CORS_METHODS` | string (comma-separated) | `*` | Allowed HTTP methods |
| `PRINTER_CORS_HEADERS` | string (comma-separated) | `*` | Allowed headers |

## Examples

### Allow Single Origin

```bash
PRINTER_CORS_ORIGINS=http://localhost:3000
```

### Allow Multiple Origins

```bash
PRINTER_CORS_ORIGINS=http://localhost:3000,https://myapp.com,https://admin.myapp.com
```

### Allow All Origins (Development Only)

```bash
PRINTER_CORS_ORIGINS=*
```

### Restrict Methods

```bash
PRINTER_CORS_METHODS=GET,POST,OPTIONS
```

## Testing CORS

Test CORS configuration with curl:

```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:9191/api/v1/initiate-print -v
```

Expected response should include:

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: POST
Access-Control-Allow-Headers: Content-Type
```

## Production Best Practices

1. **Never use `*` in production** - Always specify exact origins
2. **Use HTTPS origins** - e.g., `https://yourdomain.com`
3. **List only necessary domains** - Don't add origins you don't control
4. **Keep credentials enabled** - If using cookies/authentication
5. **Restrict methods** - Only allow needed HTTP methods

## Example Production Configuration

```bash
# .env (production)
PRINTER_CORS_ORIGINS=https://pos.restaurant.com,https://admin.restaurant.com
PRINTER_CORS_CREDENTIALS=true
PRINTER_CORS_METHODS=GET,POST,DELETE,OPTIONS
```

## Troubleshooting

### CORS Error in Browser

If you see `No 'Access-Control-Allow-Origin' header` error:

1. Check that your frontend origin is in `PRINTER_CORS_ORIGINS`
2. Ensure the origin format matches exactly (including `http://` or `https://`)
3. Verify no trailing slashes in origin URLs
4. Check browser console for the actual origin being sent

### Docker Issues

When running in Docker, use the **host machine's address**, not `localhost` inside container:

```bash
# ❌ Wrong
PRINTER_CORS_ORIGINS=http://localhost:3000

# ✅ Correct (from external access)
PRINTER_CORS_ORIGINS=http://192.168.1.100:3000
```
