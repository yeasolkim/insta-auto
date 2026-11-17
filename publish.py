"""posts/<폴더>의 사진(JPG) 또는 영상(MP4 1개 → 릴스)과 caption.txt를 인스타그램에 게시한다. GitHub Actions에서 실행."""
import glob
import os
import sys
import time
import urllib.parse

import requests

API = "https://graph.facebook.com/v24.0"
TOKEN = os.environ["IG_ACCESS_TOKEN"]  # 페이스북 페이지 토큰(만료 없음)
USER_ID = os.environ["IG_USER_ID"]  # 인스타 비즈니스 계정 ID
BASE = os.environ["IMG_BASE"].rstrip("/")


def fail(msg):
    sys.exit(f"오류: {msg}")


def check(r):
    if "error" in r:
        e = r["error"]
        fail(f"(#{e.get('code')}) {e.get('message')}")
    return r


def post(path, **data):
    data["access_token"] = TOKEN
    return check(requests.post(f"{API}/{path}", data=data, timeout=60).json())


def get(path, **params):
    params["access_token"] = TOKEN
    return check(requests.get(f"{API}/{path}", params=params, timeout=30).json())


def wait_ready(container_id, tries=40):
    for _ in range(tries):
        state = get(container_id, fields="status_code,status")
        code = state.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            fail(f"미디어 처리 실패: {state.get('status')}")
        time.sleep(3)
    fail("미디어 처리 시간 초과")


def upload_reel(user_id, video, caption, cover_url=None):
    """영상 파일을 인스타 서버로 직접 올린다(재개형 업로드). 공개 URL이 필요 없다."""
    extra = {"cover_url": cover_url} if cover_url else {}
    box = post(f"{user_id}/media", media_type="REELS", upload_type="resumable",
               caption=caption, share_to_feed="true", **extra)
    size = os.path.getsize(video)
    uri = box.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{API.rsplit('/', 1)[1]}/{box['id']}"
    with open(video, "rb") as f:
        r = requests.post(uri, data=f, timeout=600, headers={
            "Authorization": f"OAuth {TOKEN}", "offset": "0", "file_size": str(size)})
    try:
        body = r.json()
    except ValueError:
        fail(f"영상 업로드 실패: HTTP {r.status_code}")
    if not body.get("success"):
        fail(f"영상 업로드 실패: {body.get('debug_info') or body.get('error') or body}")
    return box["id"]


def main(folder):
    folder = folder.rstrip("/")
    if os.path.exists(f"{folder}/posted.txt"):
        print("이미 올린 게시물이라 건너뜀")
        return
    photos = sorted(
        p for p in glob.glob(f"{folder}/*")
        if p.lower().endswith((".jpg", ".jpeg"))
    )
    videos = sorted(p for p in glob.glob(f"{folder}/*") if p.lower().endswith(".mp4"))
    if len(videos) > 1:
        fail("영상은 1개만")
    if not photos and not videos:
        fail(f"{folder}에 JPG 사진이나 MP4 영상이 없음")
    if len(photos) > 10:
        fail("사진은 최대 10장")
    caption_path = f"{folder}/caption.txt"
    caption = open(caption_path, encoding="utf-8").read().strip() if os.path.exists(caption_path) else ""

    user_id = USER_ID
    urls = [BASE + "/" + urllib.parse.quote(p) for p in photos]

    if videos:
        # 릴스: 폴더에 JPG가 있으면 첫 장을 커버로 쓴다
        box = upload_reel(user_id, videos[0], caption, urls[0] if urls else None)
        wait_ready(box, tries=100)
    elif len(urls) == 1:
        box = post(f"{user_id}/media", image_url=urls[0], caption=caption)["id"]
    else:
        kids = []
        for u in urls:
            kid = post(f"{user_id}/media", image_url=u, is_carousel_item="true")["id"]
            wait_ready(kid)
            kids.append(kid)
        box = post(f"{user_id}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)["id"]

    wait_ready(box)
    post_id = post(f"{user_id}/media_publish", creation_id=box)["id"]
    with open(f"{folder}/posted.txt", "w") as f:
        f.write(post_id)
    link = get(post_id, fields="permalink").get("permalink", "")
    print(f"게시 완료: {post_id} {link}")


if __name__ == "__main__":
    main(sys.argv[1])
