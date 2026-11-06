#!/bin/bash
# 키체인의 인스타 토큰을 연장(60일)하고 GitHub Secret을 갱신한다.
# 발급 후 24시간 이상 지나고, 만료(60일) 전에 실행해야 한다.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")/.."

OLD=$(security find-generic-password -s insta-auto -a ig-token -w)
RES=$(curl -s "https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=$OLD")
NEW=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("access_token",""))' "$RES")
if [ -z "$NEW" ]; then
  MSG=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("error",{}).get("message","알 수 없는 오류"))' "$RES")
  echo "$(date '+%F %T') 갱신 실패: $MSG"
  osascript -e "display notification \"인스타 토큰 갱신 실패: $MSG\" with title \"insta-auto\"" || true
  exit 1
fi
security add-generic-password -U -s insta-auto -a ig-token -w "$NEW"
printf '%s' "$NEW" | gh secret set IG_ACCESS_TOKEN
echo "$(date '+%F %T') 토큰 갱신 완료"
