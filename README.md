# CROUS-BOT

Telegram bot workflow to monitor CROUS housing search results and alert on new listings.

## Features

- Polls CROUS search URL on a safe interval with jitter.
- Detects only **new** listings (deduplicated with persistent SQLite state).
- Sends Telegram alerts immediately for unseen listings.
- Supports optional smart filters (max price + keyword matching).
- Sends optional heartbeat messages and repeated-failure alerts.
- Stores secrets in environment variables (`.env`), not in code.
- Uses conservative request defaults to reduce ban/rate-limit risk.

## Project structure

- `src/main.py` CLI entrypoint
- `src/monitor.py` polling workflow and safety controls
- `src/crous_client.py` HTTP fetch + HTML parsing
- `src/state_store.py` SQLite deduplication storage
- `src/telegram_notifier.py` Telegram sender
- `src/config.py` runtime configuration loader

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

3. Create `.env` from template:

	```bash
	cp .env.example .env
	```

4. Fill required values in `.env`.

## Required environment variables

- `CROUS_SEARCH_URL` (your CROUS search URL)
- `TELEGRAM_BOT_TOKEN` (token from BotFather)
- `TELEGRAM_CHAT_ID` (chat/user ID that receives alerts)

Optional:

- `FILTER_MAX_PRICE_EUR` (only alert when listing price is <= this value)
- `FILTER_INCLUDE_KEYWORDS` (comma-separated keywords that must match title/city/residence/url)
- `HEARTBEAT_ENABLED` (`true|false`, default `false`)
- `HEARTBEAT_INTERVAL_HOURS` (default `168`)
- `ERROR_ALERT_THRESHOLD` (default `3` consecutive failures)
- `ERROR_ALERT_COOLDOWN_MINUTES` (default `180`)

## Run

Dry run (no Telegram sends, useful for testing parser):

```bash
python -m src.main --once --dry-run --debug
```

Send a single Telegram healthcheck message (one-shot):

```bash
python -m src.main --once --test-telegram
```

Continuous monitor:

```bash
python -m src.main
```

## Run 24/7 with GitHub Actions

GitHub Actions can run this monitor every 5 minutes (GitHub minimum schedule granularity).

1. Push this repository to GitHub.
2. In your repo, open **Settings → Secrets and variables → Actions**.
3. Add these repository secrets:
	- `CROUS_SEARCH_URL`
	- `TELEGRAM_BOT_TOKEN`
	- `TELEGRAM_CHAT_ID`
4. Enable the workflow in **Actions** tab (`CROUS Monitor`).
5. Optional: trigger manually with **Run workflow**.
	- Set `test_telegram=true` to send one healthcheck Telegram message immediately.

Workflow file: `.github/workflows/crous-monitor.yml`

### Notes

- Dedup state is persisted between workflow runs using GitHub cache.
- First run initializes state; alerts start for newly discovered unseen listings.
- If cache is evicted by GitHub, dedup history resets and previously seen listings may alert again.
- Manual runs can send a one-shot Telegram test with `test_telegram=true`.
- Heartbeat is enabled in the GitHub workflow and sends only when interval is reached.
- Failure alerts are sent only after repeated consecutive failures (to avoid alert noise).

### Telegram commands (dynamic filters)

Commands are checked automatically on each workflow run, then applied to filtering:

- `/showfilters`
- `/setmaxprice <eur>`
- `/clearmaxprice`
- `/setkeywords kw1,kw2`
- `/clearkeywords`
- `/help`

Example:

- Send `/setmaxprice 350`
- Send `/setkeywords strasbourg,igbmc`

The next scheduled run applies them and confirms back in Telegram.

## Safety defaults

- Poll interval default: `180s`
- Jitter default: `20s`
- Request timeout: `15s`
- Retries: low, with backoff

Tune these through environment variables if needed.

## Security notes

- Never commit `.env`.
- Rotate Telegram token if leaked.
- Keep logs free from secrets and personal data.
