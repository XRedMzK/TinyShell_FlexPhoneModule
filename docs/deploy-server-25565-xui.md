# FlexPhone Backend Deploy Guide (порт 25565, 443 занят x-ui)

Ниже пошаговый деплой backend так, чтобы:
- x-ui продолжал использовать `443`;
- FlexPhone backend был доступен по `https://<домен>:25565`.

## 1. Что получится по итогу

- FastAPI/WS backend работает как `systemd` сервис на `127.0.0.1:18000`.
- Redis работает в Docker на `127.0.0.1:6379`.
- Nginx публикует backend наружу на `25565` (TLS).

## 2. Подготовка сервера

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx
```

Открыть порт в firewall (если включен UFW):

```bash
sudo ufw allow 25565/tcp
```

## 3. Клонирование и установка backend

```bash
sudo mkdir -p /opt/flexphone
sudo chown -R $USER:$USER /opt/flexphone
cd /opt/flexphone
git clone https://github.com/XRedMzK/TinyShell_FlexPhoneModule.git .

cd /opt/flexphone/server
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Redis (Docker)

```bash
docker rm -f flexphone-redis >/dev/null 2>&1 || true
docker run -d \
  --name flexphone-redis \
  --restart unless-stopped \
  -p 127.0.0.1:6379:6379 \
  redis:7-alpine
```

Проверка:

```bash
docker ps --filter name=flexphone-redis
```

## 5. Конфиг окружения backend

Создай `/etc/flexphone/flexphone.env`:

```bash
sudo mkdir -p /etc/flexphone
sudo tee /etc/flexphone/flexphone.env >/dev/null <<'EOF'
FLEXPHONE_APP_NAME=FlexPhone Server
FLEXPHONE_DEBUG=false

# Добавь реальные origin-ы клиента:
# - tauri://localhost (desktop)
# - https://your-domain.example:25565 (если тестируешь web UI)
FLEXPHONE_ALLOWED_ORIGINS=tauri://localhost,https://your-domain.example:25565

FLEXPHONE_AUTH_CHALLENGE_REDIS_URL=redis://127.0.0.1:6379/0
FLEXPHONE_SIGNALING_REDIS_URL=redis://127.0.0.1:6379/0

FLEXPHONE_AUTH_JWT_SECRET=CHANGE_ME_TO_LONG_RANDOM_SECRET

# TURN (рекомендуется для реальных звонков):
# либо секрет для ephemeral creds:
# FLEXPHONE_WEBRTC_TURN_AUTH_SECRET=CHANGE_ME
# либо static creds:
# FLEXPHONE_WEBRTC_TURN_USERNAME=flexphone
# FLEXPHONE_WEBRTC_TURN_PASSWORD=CHANGE_ME
EOF
```

## 6. systemd сервис backend

Создай системного пользователя:

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin flexphone || true
sudo chown -R flexphone:flexphone /opt/flexphone/server
```

Установи unit:

```bash
sudo cp /opt/flexphone/server/deploy/systemd/flexphone-server.service /etc/systemd/system/flexphone-server.service
sudo systemctl daemon-reload
sudo systemctl enable --now flexphone-server
```

Проверка:

```bash
sudo systemctl status flexphone-server --no-pager
curl -sS http://127.0.0.1:18000/health
```

## 7. Публикация через Nginx на 25565

1. Скопируй шаблон:

```bash
sudo cp /opt/flexphone/server/deploy/nginx/flexphone-25565.conf /etc/nginx/sites-available/flexphone-25565.conf
```

2. Отредактируй:
- `server_name`;
- пути к `ssl_certificate` и `ssl_certificate_key`.

3. Включи сайт:

```bash
sudo ln -sf /etc/nginx/sites-available/flexphone-25565.conf /etc/nginx/sites-enabled/flexphone-25565.conf
sudo nginx -t
sudo systemctl reload nginx
```

Проверка:

```bash
curl -sS https://your-domain.example:25565/health
```

## 8. Сертификаты при занятом 443

Так как `443` занят x-ui:
- не используй этот порт для FlexPhone;
- FlexPhone публикуется на `25565` по TLS;
- сертификат можно получить отдельно (например, DNS challenge) и положить в пути, указанные в nginx-конфиге.

## 9. Полезные команды эксплуатации

Логи backend:

```bash
sudo journalctl -u flexphone-server -f
```

Перезапуск backend:

```bash
sudo systemctl restart flexphone-server
```

Обновление backend:

```bash
cd /opt/flexphone
git pull
cd /opt/flexphone/server
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart flexphone-server
```

---

Если нужно, следующим шагом соберу отдельный чек-лист для клиентской сборки с endpoint `https://your-domain.example:25565` и проверкой WS/WebRTC под этот прод-конфиг.
