"""
One-time setup script: получить OAuth2 refresh_token от личного Google-аккаунта.

Шаги:
  1. Открой: https://console.cloud.google.com/apis/credentials
  2. Создай OAuth 2.0 Client ID → Desktop App (или Web)
  3. Скачай JSON и скопируй client_id и client_secret
  4. Запусти этот скрипт: python setup_google_oauth.py
  5. Вставь в .env:  GOOGLE_OAUTH_REFRESH_TOKEN=...
"""
import webbrowser
import urllib.parse
import urllib.request
import json
import sys

CLIENT_ID     = input("Введи GOOGLE_OAUTH_CLIENT_ID: ").strip()
CLIENT_SECRET = input("Введи GOOGLE_OAUTH_CLIENT_SECRET: ").strip()

REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
SCOPE = (
    "https://www.googleapis.com/auth/drive "
    "https://www.googleapis.com/auth/documents"
)

auth_url = (
    "https://accounts.google.com/o/oauth2/auth"
    f"?client_id={urllib.parse.quote(CLIENT_ID)}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&response_type=code"
    f"&scope={urllib.parse.quote(SCOPE)}"
    f"&access_type=offline"
    f"&prompt=consent"
)

print("\nОткрывается браузер для авторизации...")
print(f"\nЕсли не открылся — перейди по ссылке:\n{auth_url}\n")
webbrowser.open(auth_url)

code = input("Вставь код из браузера: ").strip()

data = urllib.parse.urlencode({
    "code":          code,
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri":  REDIRECT_URI,
    "grant_type":    "authorization_code",
}).encode()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
try:
    resp = json.loads(urllib.request.urlopen(req).read())
except urllib.error.HTTPError as e:
    print(f"Ошибка: {e.read().decode()}")
    sys.exit(1)

refresh_token = resp.get("refresh_token", "")
if not refresh_token:
    print(f"Токен не получен. Ответ: {resp}")
    sys.exit(1)

print("\n✅  Добавь в .env:\n")
print(f"GOOGLE_OAUTH_CLIENT_ID={CLIENT_ID}")
print(f"GOOGLE_OAUTH_CLIENT_SECRET={CLIENT_SECRET}")
print(f"GOOGLE_OAUTH_REFRESH_TOKEN={refresh_token}")
print("\nЗатем перезапусти backend.")
