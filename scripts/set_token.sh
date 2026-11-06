#!/bin/bash
# 페이스북(통합 로그인) 토큰으로 "만료 없는 페이지 토큰"을 만들어 GitHub Secret에 등록한다.
# 입력값은 화면·파일에 남지 않는다. 처음 한 번만 실행하면 된다(비밀번호 변경·앱 권한 해제 시 다시).
set -euo pipefail
cd "$(dirname "$0")/.."
G=https://graph.facebook.com/v24.0
APP_ID=1450101423141787
PAGE_ID=1036493289554096   # 니팅인더사우나 - 뜨개 도안 트래커

json() { python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(eval(sys.argv[2]))" "$1" "$2"; }

read -rsp "토큰 생성에서 받은 EAA... 토큰: " SHORT; echo
read -rsp "앱 시크릿 코드(앱 설정 > 기본 설정): " SECRET; echo

R=$(curl -s "$G/oauth/access_token?grant_type=fb_exchange_token&client_id=$APP_ID&client_secret=$SECRET&fb_exchange_token=$SHORT")
LONG=$(json "$R" 'd.get("access_token","")')
[ -n "$LONG" ] || { echo "장기 토큰 교환 실패: $(json "$R" 'd.get("error",{}).get("message")')"; exit 1; }

R=$(curl -s "$G/$PAGE_ID?fields=access_token,name,instagram_business_account{id,username}&access_token=$LONG")
PAGE_TOKEN=$(json "$R" 'd.get("access_token","")')
IG_ID=$(json "$R" 'd.get("instagram_business_account",{}).get("id","")')
IG_NAME=$(json "$R" 'd.get("instagram_business_account",{}).get("username","")')
[ -n "$PAGE_TOKEN" ] || { echo "페이지 토큰 실패: $(json "$R" 'd.get("error",{}).get("message")')"; exit 1; }
[ -n "$IG_ID" ] || { echo "페이지에 연결된 인스타 비즈니스 계정이 없음"; exit 1; }

R=$(curl -s "$G/debug_token?input_token=$PAGE_TOKEN&access_token=$APP_ID|$SECRET")
EXP=$(json "$R" 'd.get("data",{}).get("expires_at","?")')
echo "확인됨: @$IG_NAME (ID $IG_ID), 페이지 토큰 만료: $([ "$EXP" = "0" ] && echo 없음 || echo "$EXP")"

printf '%s' "$PAGE_TOKEN" | gh secret set IG_ACCESS_TOKEN
printf '%s' "$IG_ID" | gh secret set IG_USER_ID
echo "GitHub Secret 등록 완료"
