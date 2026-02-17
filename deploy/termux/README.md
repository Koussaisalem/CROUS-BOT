# Run on Android (Termux)

This setup lets your phone run the monitor without a VPS.

## Important limits

- Android may stop background apps (battery optimizations / Doze).
- True 24/7 is **not guaranteed** on phones, but this is the best practical setup.

## 1) Install apps

- Install **Termux** from F-Droid (recommended).
- Optional but useful: **Termux:Boot** (auto-start on reboot).

## 2) Install packages

In Termux:

```bash
pkg update -y && pkg upgrade -y
pkg install -y python git
```

## 3) Clone and install bot

```bash
cd ~
git clone https://github.com/Koussaisalem/CROUS-BOT.git crous-bot
cd crous-bot
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with real values:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `CROUS_SEARCH_URL`

## 4) Test once

```bash
cd ~/crous-bot
python -m src.main --once --dry-run --debug
```

## 5) Start continuous monitor

```bash
cd ~/crous-bot
chmod +x deploy/termux/start_monitor.sh
./deploy/termux/start_monitor.sh
```

Logs:

```bash
tail -f ~/crous-bot/logs/monitor.log
```

## 6) Improve reliability on phone

1. Disable battery optimization for Termux in Android settings.
2. Keep Termux notification enabled (do not swipe it away).
3. In Termux, keep CPU awake while running:

   ```bash
   termux-wake-lock
   ```

4. Optional auto-start after reboot (Termux:Boot):

   ```bash
   mkdir -p ~/.termux/boot
   cat > ~/.termux/boot/start-crous.sh << 'EOF'
   #!/data/data/com.termux/files/usr/bin/bash
   cd "$HOME/crous-bot"
   ./deploy/termux/start_monitor.sh
   EOF
   chmod +x ~/.termux/boot/start-crous.sh
   ```

## Safety defaults

Current defaults are conservative enough for phone usage:

- `POLL_INTERVAL_SECONDS=180`
- `POLL_JITTER_SECONDS=20`

You can increase interval (for example `240` or `300`) to reduce request pressure and battery drain.
