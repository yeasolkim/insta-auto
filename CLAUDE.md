# insta-auto

인스타그램 자동 게시 레포. 사진은 이 공개 레포의 raw URL로 인스타 API에 전달된다(올리기 전에도 공개됨).

## "인스타 올려줘" 요청을 받으면
1. 올릴 사진 폴더(JPG/PNG 1~10장 + caption.txt)를 확인한다. 없으면 만들어 준다.
2. `python3 scripts/post.py <폴더> --dry-run` 으로 순서·캡션·비율을 검사하고 사용자에게 보여준다.
3. 사용자가 "이대로 올릴까요?"에 확인하면 실행:
   - 즉시: `python3 scripts/post.py <폴더>`
   - 예약: `python3 scripts/post.py <폴더> YYYY-MM-DD` (그날 오전 9시 KST 무렵, 하루 1개)
4. 결과(게시 링크 또는 오류)를 알려준다. 게시는 되돌리기 어려우니 확인 없이 올리지 않는다.

## 오류 대처
- `#190` 토큰 만료/무효 → `bash scripts/refresh_token.sh`, 이미 만료(60일 경과)면 앱 대시보드에서 새 토큰 발급 후 사용자가 직접 터미널에서 `bash scripts/set_token.sh`
- `#10` / permission → Meta 앱에 `instagram_business_content_publish` 권한 추가 후 토큰 재발급
- `#9` / 비율 오류 → 4:5 ~ 1.91:1로 자르기
- 예약 확인: `ls posts/` (posted.txt 있으면 게시 완료)
- 예약 취소: 해당 `posts/<날짜>` 폴더 삭제 후 커밋·푸시

## 구성
- `publish.py` / `.github/workflows/publish.yml`: Actions에서 게시. 매일 00:00 UTC에 `posts/<오늘 날짜>` 확인
- `scripts/post.py`: 로컬에서 폴더 업로드 + 워크플로 실행
- `scripts/set_token.sh`: 토큰 등록(키체인 + GitHub Secret `IG_ACCESS_TOKEN`, `IG_USER_ID`)
- `scripts/refresh_token.sh`: 토큰 60일 연장 (수동 실행, 50일 안에)
- GitHub 인증은 로컬 `gh` CLI 로그인을 사용 (별도 PAT 없음)
