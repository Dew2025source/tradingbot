# Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI for placing orders on the [Binance Futures USDT-M Testnet](https://testnet.binancefuture.com).

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Low-level HMAC-signed REST client
│   ├── orders.py          # Order placement logic + OrderResult model
│   ├── validators.py      # Input validation (raises ValidationError)
│   └── logging_config.py  # Rotating file + console logging
├── cli.py                 # argparse CLI entry point
├── logs/
│   ├── market_order.log   # Sample MARKET order log
│   └── limit_order.log    # Sample LIMIT order log
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Register on Binance Futures Testnet

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Sign up / log in (GitHub OAuth is supported)
3. Navigate to **API Management** → **Create API**
4. Copy your **API Key** and **Secret Key**

### 2. Install dependencies

```bash
# Python 3.8+ required
pip install -r requirements.txt
```

### 3. Set credentials

**Option A – Environment variables (recommended):**

```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```
**if you are using windows**
```bash
$env BINANCE_API_KEY="your_api_key_here"
$env BINANCE_API_SECRET="your_api_secret_here"
```
**Option B – CLI flags** (see examples below)

---

## How to Run

### Market Order (BUY)

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001
```

### Limit Order (SELL)

```bash
python cli.py \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.001 \
  --price 70000
```

### Stop-Limit Order (BONUS – triggers at 67500, places limit at 68000)

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --type STOP_LIMIT \
  --quantity 0.001 \
  --price 68000 \
  --stop-price 67500
```

### Passing credentials inline

```bash
python cli.py \
  --api-key YOUR_KEY \
  --api-secret YOUR_SECRET \
  --symbol ETHUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.01
```

### Verbose debug logging (console)

```bash
python cli.py --log-level DEBUG --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

---

## Sample Output

```
┌── Order Request Summary ─────────────────────────────
│  Symbol     : BTCUSDT
│  Side       : BUY
│  Type       : MARKET
│  Quantity   : 0.001
└──────────────────────────────────────────────────────

✔  Order placed successfully!

──────────────────────────────────────────────────
  Order ID     : 4381290
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Status       : FILLED
  Orig Qty     : 0.001
  Executed Qty : 0.001
  Avg Price    : 67832.50
  Client OID   : x-Cb7ytekJb8f3d3f7c0f4
──────────────────────────────────────────────────
```

---

## Logging

All runs are appended to `logs/trading_bot.log` (rotating, up to 10 MB across 5 files).

| Level   | Where             | Content                                      |
|---------|-------------------|----------------------------------------------|
| DEBUG   | file only         | Full request params, raw response bodies     |
| INFO    | file + console    | Order summary, success/failure               |
| WARNING | file + console    | Ignored params (e.g. price on MARKET order)  |
| ERROR   | file + console    | API errors, validation failures              |

Sample log files are included in `logs/`:
- `logs/market_order.log` – BUY MARKET 0.001 BTCUSDT (FILLED)
- `logs/limit_order.log`  – SELL LIMIT 0.001 BTCUSDT @ 70000 (NEW)

---

## Error Handling

| Scenario               | Behaviour                                                    |
|------------------------|--------------------------------------------------------------|
| Missing credentials    | Clear message + `sys.exit(1)`                               |
| Invalid input          | `ValidationError` caught, descriptive message, `exit(2)`   |
| Binance API error      | `BinanceAPIError` with HTTP status + Binance code, `exit(3)` |
| Network timeout        | Caught, logged, `exit(3)`                                   |
| Unexpected exception   | Full traceback logged to file, clean message on console     |

---

## Assumptions

- Only **USDT-M Futures Testnet** is targeted (`https://testnet.binancefuture.com`).
- **MARKET** orders ignore any `--price` argument (warning is logged).
- **LIMIT** orders use `timeInForce=GTC` by default.
- **STOP_LIMIT** maps to Binance's `STOP` futures order type (stop-limit on futures).
- Quantity precision must satisfy the symbol's `LOT_SIZE` filter; the bot does **not** auto-round — use appropriate precision for your symbol (0.001 for BTCUSDT).
- Credentials are never logged.

---

## Requirements

```
requests>=2.31.0
```

Python standard library only otherwise (`argparse`, `hmac`, `hashlib`, `decimal`, `logging`, `dataclasses`).
