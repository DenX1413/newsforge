# Запуск веб-версии

## 1. Установи Node.js (если нет)
Скачай с https://nodejs.org → версия LTS → установи

## 2. Бэкенд
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn api:app --reload --port 8000
```

## 3. Фронтенд
```bash
cd frontend
npm install
npm run dev
```

## 4. Открой
http://localhost:5173
