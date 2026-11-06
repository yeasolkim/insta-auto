#!/bin/bash
# 인스타 토큰을 등록한다. 토큰은 키체인과 GitHub Secret에만 저장되고 화면·파일에 남지 않는다.
# 처음 한 번, 그리고 토큰이 만료돼 새로 발급했을 때 실행.
set -euo pipefail
cd "$(dirname "$0")/.."

read -rsp "인스타 액세스 토큰(IGAA...) 붙여넣고 Enter: " TOKEN; echo
[ -n "$TOKEN" ] || { echo "토큰이 비었음"; exit 1; }

ME=$(curl -s "https://graph.instagram.com/v21.0/me?fields=user_id,username&access_token=$TOKEN")
USER_ID=$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("user_id",""))' "$ME")
USERNAME=$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("username",""))' "$ME")
[ -n "$USER_ID" ] || { echo "토큰 확인 실패: $ME"; exit 1; }
echo "확인됨: @$USERNAME (ID $USER_ID)"

security add-generic-password -U -s insta-auto -a ig-token -w "$TOKEN"
printf '%s' "$TOKEN" | gh secret set IG_ACCESS_TOKEN
printf '%s' "$USER_ID" | gh secret set IG_USER_ID
echo "키체인과 GitHub Secret에 저장 완료"
bash scripts/install_refresh.sh
