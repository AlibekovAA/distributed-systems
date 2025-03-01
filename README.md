## Запуск проекта

1. Запусти Docker Compose:

   ```bash
   docker-compose up --build
   ```

2. После успешного запуска:

   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Auth Service API**: [http://localhost:8000/auth](http://localhost:8000/auth)
   - **PgAdmin**: [http://localhost:5050](http://localhost:5050)

## Доступ к сервисам

### Frontend
- Откройте [http://localhost:3000](http://localhost:3000)
- Доступны функции регистрации и входа
- Навигация по разделам:
  - Профиль пользователя
  - Каталог товаров
  - Корзина покупок

### Auth Service API
- Swagger документация: [http://localhost:8000/docs](http://localhost:8000/docs)
- Основные эндпоинты:
  - POST `/auth/register` - регистрация
  - POST `/auth/login` - вход
  - GET `/auth/profile` - профиль пользователя
  - POST `/auth/change-password` - смена пароля
  - POST `/auth/add-balance` - пополнение баланса
  - POST `/auth/token/refresh` - обновление токена

### База данных (через pgAdmin)
1. Откройте [http://localhost:5050](http://localhost:5050)
2. Войдите в pgAdmin:
   - Email: `admin@admin.com`
   - Password: `admin`
3. Добавьте новый сервер:
   - Host: `db`
   - Port: `5432`
   - Database: `mydatabase`
   - Username: `user`
   - Password: `password`

## Разработка

### Frontend
- Исходный код фронтенда находится в `frontend/src/`
- Модули разделены по папкам в `src/modules/`
- Общие стили в `src/styles/common/`
- Сервисы для работы с API в `src/services/`
- Утилиты и вспомогательные функции в `src/utils/`

### Backend
- Сервис аутентификации в `backend/auth-service/`
- Модульная структура:
  - `app/` - основной код приложения
  - `models/` - модели данных
  - `services/` - бизнес-логика
  - `tests/` - тесты

## Очистка Docker окружения

```bash
docker stop $(docker ps -a -q)

docker rm $(docker ps -a -q)

docker rmi $(docker images -q)

docker system prune -a --volumes -f
```
