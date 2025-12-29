#!/usr/bin/env python3
import os
import sys
import time
import json
import base64
import re
import random
import requests
from playwright.sync_api import sync_playwright

CLAW_CLOUD_URL = "https://eu-central-1.run.claw.cloud"
SIGNIN_URL = f"{CLAW_CLOUD_URL}/signin"
DEVICE_VERIFY_WAIT = 30
TWO_FACTOR_WAIT = int(os.environ.get("TWO_FACTOR_WAIT", "120"))


# ==================== Telegram ====================
class Telegram:
    def __init__(self):
        self.token = os.environ.get("TG_BOT_TOKEN")
        self.chat_id = os.environ.get("TG_CHAT_ID")
        self.ok = bool(self.token and self.chat_id)

    def send(self, msg):
        if not self.ok:
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                data={"chat_id": self.chat_id, "text": msg, "parse_mode": "HTML"},
                timeout=30,
            )
        except:
            pass

    def photo(self, path, caption=""):
        if not self.ok or not os.path.exists(path):
            return
        try:
            with open(path, "rb") as f:
                requests.post(
                    f"https://api.telegram.org/bot{self.token}/sendPhoto",
                    data={"chat_id": self.chat_id, "caption": caption[:1024]},
                    files={"photo": f},
                    timeout=60,
                )
        except:
            pass


# ==================== GitHub Secret ====================
class SecretUpdater:
    def __init__(self):
        self.token = os.environ.get("REPO_TOKEN")
        self.repo = os.environ.get("GITHUB_REPOSITORY")
        self.ok = bool(self.token and self.repo)

    def update(self, name, value):
        if not self.ok:
            return False
        try:
            from nacl import encoding, public

            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            r = requests.get(
                f"https://api.github.com/repos/{self.repo}/actions/secrets/public-key",
                headers=headers,
                timeout=30,
            )
            key = r.json()
            pk = public.PublicKey(
                key["key"].encode(), encoding.Base64Encoder()
            )
            encrypted = public.SealedBox(pk).encrypt(value.encode())

            r = requests.put(
                f"https://api.github.com/repos/{self.repo}/actions/secrets/{name}",
                headers=headers,
                json={
                    "encrypted_value": base64.b64encode(encrypted).decode(),
                    "key_id": key["key_id"],
                },
                timeout=30,
            )
            return r.status_code in (201, 204)
        except:
            return False


# ==================== AutoLogin（单账号） ====================
class AutoLogin:
    def __init__(self, acc: dict):
        self.acc = acc
        self.name = acc.get("name", acc["username"])
        self.username = acc["username"]
        self.password = acc["password"]
        self.gh_session = acc.get("session", "").strip()
        self.secret_name = acc.get("secret", "GH_SESSION")

        self.tg = Telegram()
        self.secret = SecretUpdater()
        self.logs = []
        self.shots = []
        self.n = 0

    def log(self, msg, level="INFO"):
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️", "STEP": "🔹"}
        line = f"{icons.get(level,'•')} [{self.name}] {msg}"
        print(line)
        self.logs.append(line)

    def shot(self, page, name):
        self.n += 1
        f = f"{self.name}_{self.n:02d}_{name}.png"
        try:
            page.screenshot(path=f)
            self.shots.append(f)
        except:
            pass

    def get_session(self, context):
        for c in context.cookies():
            if c["name"] == "user_session" and "github" in c.get("domain", ""):
                return c["value"]
        return None

    def save_cookie(self, value):
        if not value:
            return
        if self.secret.update(self.secret_name, value):
            self.tg.send(
                f"🔑 <b>{self.name}</b>\nCookie 已更新\n<code>{self.secret_name}</code>"
            )
        else:
            self.tg.send(
                f"🔑 <b>{self.name}</b>\n请手动更新 <code>{self.secret_name}</code>\n<code>{value}</code>"
            )

    def keepalive(self, page):
        for p in ["/", "/apps", "/settings"]:
            try:
                page.goto(f"{CLAW_CLOUD_URL}{p}", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(random.randint(2, 4))
            except:
                pass

    def run(self):
        self.log("开始执行", "STEP")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )

            if self.gh_session:
                context.add_cookies([
                    {
                        "name": "user_session",
                        "value": self.gh_session,
                        "domain": "github.com",
                        "path": "/",
                    }
                ])

            page = context.new_page()

            page.goto(SIGNIN_URL, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)

            if "signin" not in page.url.lower():
                self.log("Cookie 有效，已登录", "SUCCESS")
            else:
                page.locator('button:has-text("GitHub")').first.click()
                page.wait_for_load_state("networkidle", timeout=30000)

                if "github.com/login" in page.url:
                    page.fill('input[name="login"]', self.username)
                    page.fill('input[name="password"]', self.password)
                    page.click('input[type="submit"]')
                    page.wait_for_load_state("networkidle", timeout=30000)

            # OAuth
            if "oauth" in page.url:
                try:
                    page.click('button:has-text("Authorize")')
                except:
                    pass

            # 等回 ClawCloud
            for _ in range(60):
                if "claw.cloud" in page.url and "signin" not in page.url:
                    break
                time.sleep(1)

            self.keepalive(page)

            new_cookie = self.get_session(context)
            if new_cookie:
                self.save_cookie(new_cookie)

            browser.close()
            self.log("完成", "SUCCESS")


# ==================== 多账号入口 ====================
def load_accounts():
    raw = os.environ.get("GH_ACCOUNTS")
    if not raw:
        raise RuntimeError("未配置 GH_ACCOUNTS")
    return json.loads(raw)


if __name__ == "__main__":
    accounts = load_accounts()

    for i, acc in enumerate(accounts, 1):
        print("\n" + "=" * 60)
        print(f"🚀 账号 {i}/{len(accounts)}: {acc.get('name')}")
        print("=" * 60)

        try:
            AutoLogin(acc).run()
        except Exception as e:
            print(f"❌ 失败: {e}")

        time.sleep(random.randint(8, 15))
