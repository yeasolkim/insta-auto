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
- `#190` 토큰 만료/무효 → 앱 대시보드 > API setup with Unified login > 토큰 생성으로 새 토큰 발급 후 사용자가 직접 터미널에서 `bash scripts/set_token.sh`
- `#10` / permission → 통합 로그인 구성에 `instagram_basic`, `instagram_content_publish` 권한 확인 후 토큰 재발급
- `#9` / 비율 오류 → 4:5 ~ 1.91:1로 자르기
- 예약 확인: `ls posts/` (posted.txt 있으면 게시 완료)
- 예약 취소: 해당 `posts/<날짜>` 폴더 삭제 후 커밋·푸시

## 구성
- `publish.py` / `.github/workflows/publish.yml`: Actions에서 게시. 매일 00:00 UTC에 `posts/<오늘 날짜>` 확인
- `scripts/post.py`: 로컬에서 폴더 업로드 + 워크플로 실행
- API: graph.facebook.com, Instagram API with Unified login (새 앱은 Instagram 로그인 방식 사용 불가). 토큰은 시스템 사용자 토큰(SUAT), 페이지 불필요
- `scripts/set_token.sh`: 토큰 → `/me/assigned_instagram_accounts`로 계정 ID 확인 → GitHub Secret `IG_ACCESS_TOKEN`, `IG_USER_ID`
- 인스타 계정 @knitting_in_the_sauna = 17841476496692787, 앱 ID 1450101423141787
- GitHub 인증은 로컬 `gh` CLI 로그인을 사용 (별도 PAT 없음)
