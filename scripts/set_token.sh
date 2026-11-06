#!/bin/bash
# 통합 로그인(Unified login)으로 만든 시스템 사용자 토큰(SUAT, EAA...)을 GitHub Secret에 등록한다.
# 토큰 발급: 앱 대시보드 > 이용 사례 > Instagram에서 메시지 및 콘텐츠 관리 > 맞춤 설정
#           > API setup with Unified login > 토큰 생성 (한 번만 표시됨)
# 토큰이 만료·무효가 됐을 때(오류 #190) 새로 발급해서 다시 실행.
set -euo pipefail
cd "$(dirname "$0")/.."
G=https://graph.facebook.com/v24.0

read -rsp "EAA... 토큰 붙여넣고 Enter: " TOKEN; echo
R=$(curl -s "$G/me/assigned_instagram_accounts?fields=id,username&access_token=$TOKEN")
read -r IG_ID IG_NAME < <(python3 -c '
import json,sys; d=json.loads(sys.argv[1])
if "error" in d: sys.exit("토큰 확인 실패: " + d["error"].get("message",""))
a=d.get("data",[]); print(a[0]["id"], a[0]["username"]) if a else sys.exit("연결된 인스타 계정이 없음")' "$R")
echo "확인됨: @$IG_NAME (ID $IG_ID)"

printf '%s' "$TOKEN" | gh secret set IG_ACCESS_TOKEN
printf '%s' "$IG_ID" | gh secret set IG_USER_ID
echo "GitHub Secret 등록 완료"
