"""posts/<폴더>의 사진(JPG)과 caption.txt를 인스타그램에 게시한다. GitHub Actions에서 실행."""
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


def wait_ready(container_id):
    for _ in range(40):
        state = get(container_id, fields="status_code,status")
        code = state.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            fail(f"미디어 처리 실패: {state.get('status')}")
        time.sleep(3)
    fail("미디어 처리 시간 초과")


def main(folder):
    folder = folder.rstrip("/")
    if os.path.exists(f"{folder}/posted.txt"):
        print("이미 올린 게시물이라 건너뜀")
        return
    photos = sorted(
        p for p in glob.glob(f"{folder}/*")
        if p.lower().endswith((".jpg", ".jpeg"))
    )
    if not photos:
        fail(f"{folder}에 JPG 사진이 없음")
    if len(photos) > 10:
        fail("사진은 최대 10장")
    caption_path = f"{folder}/caption.txt"
    caption = open(caption_path, encoding="utf-8").read().strip() if os.path.exists(caption_path) else ""

    user_id = USER_ID
    urls = [BASE + "/" + urllib.parse.quote(p) for p in photos]

    if len(urls) == 1:
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
