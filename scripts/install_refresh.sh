#!/bin/bash
# 토큰 자동 갱신을 macOS launchd에 등록한다 (매주 월요일 오전 10시, 그 시간에 맥이 잠자기였으면 깨어난 뒤 실행).
# 해제: launchctl unload ~/Library/LaunchAgents/com.yeasolkim.insta-auto-refresh.plist && rm 그 파일
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.yeasolkim.insta-auto-refresh.plist"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.yeasolkim.insta-auto-refresh</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$DIR/scripts/refresh_token.sh</string></array>
  <key>StartCalendarInterval</key><dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/insta-auto-refresh.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/insta-auto-refresh.log</string>
</dict></plist>
EOF
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "토큰 자동 갱신 등록 완료 (매주 월요일 10시, 로그: ~/Library/Logs/insta-auto-refresh.log)"
