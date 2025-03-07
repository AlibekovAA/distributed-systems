## Запуск проекта

1. Запусти Docker Compose:

   ```bash
   docker-compose up --build
   ```

2. После успешного запуска:

   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Auth Service API**: [http://localhost:8000/auth](http://localhost:8000/auth)
   - **PgAdmin**: [http://localhost:5050](http://localhost:5050)
   - **Product Catalog Service**: [http://localhost:8080](http://localhost:8080)

## Доступ к сервисам

### Recommendation service
- Основные функции:
  - Персонализированные рекомендации всех товаров на основе:
    - Истории покупок пользователя
    - Предпочтений пользователя
    - Категорий товаров
    - Доступности товаров

- Алгоритм рекомендаций использует комбинированный подход для расчета рейтинга каждого товара:
  - 50% - учет предпочтений пользователя
  - 40% - анализ категорий из истории покупок
  - 10% - доступность товара на складе

- Процесс формирования рекомендаций:
  1. Анализ истории покупок пользователя
  2. Учет заполненной анкеты предпочтений
  3. Расчет весов категорий на основе истории
  4. Вычисление рейтинга для каждого товара в каталоге
  5. Сортировка всех товаров по убыванию рейтинга
  6. Возврат полного списка товаров с их рейтингами рекомендаций

- Интеграция:
  - Работает через RabbitMQ для асинхронной обработки
  - Автоматически обновляет рекомендации при новых покупках

### Frontend
- Доступны функции регистрации, входа и страница профиля пользователя.
- Навигация по разделам:
  - Профиль пользователя
  - Каталог товаров
  - Корзина покупок

### Auth Service API
- Основные эндпоинты:
  - POST `/auth/register` - регистрация
  - POST `/auth/login` - вход
  - GET `/auth/profile` - профиль пользователя
  - POST `/auth/change-password` - смена пароля
  - POST `/auth/add-balance` - пополнение баланса
  - POST `/auth/token/refresh` - обновление токена
  - GET `/auth/health` - проверка состояния сервиса
  - GET `/preferences/check` - проверка наличия заполненной анкеты предпочтений у пользователя
  - POST `/preferences/save` - сохранение заполненной анкеты предпочтений пользователя

### Product Catalog Service API
- Основные эндпоинты:
  - GET `/products/{email}` - получение списка всех товаров
  - POST `/products` - создание нового товара
  - DELETE `/products` - удаление товара
  - GET `/order/{email}` - получение корзины пользователя
  - POST `/order/add` - добавление товара в корзину
  - DELETE `/order/{email}/{product_id}` - удаление товара из корзины
  - POST `/order/{email}/pay` - оплата заказа
  - GET `/orders/{email}/history` - история заказов пользователя

### Swagger документация
В проекте используется объединенная Swagger-документация для сервисов, написанных на FastAPI и Golang.
1. Запуск swagger UI:
   ```bash
   cd swagger
   python swagger.py
   ```
2. Просмотр Swagger:
   - Swagger UI: `https://petstore.swagger.io/?url=http://localhost:4040/combined-swagger.json`
3. Для остановки сервера нажмите Enter в консоли.

Для остановки сервера нажмите Enter в консоли.
### База данных (через pgAdmin)
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
- Сервис рекомендаций в `backend/recommendation-service/`
- Модульная структура:
  - `app/` - основной код приложения
  - `models/` - модели данных
- Сервис каталога товаров в `backend/product-catalog-service/`
- Модульная структура:
  - `src/application/` - обработчики HTTP запросов
  - `src/config/` - конфигурация приложения
  - `src/db/` - работа с базой данных
  - `src/models/` - модели данных
  - `src/docs/` - Swagger документация

## Тестирование

1. Запуск тестов:
   ```bash
   cd tests
   python run_tests.py
   ```
2. Просмотр отчетов:
   - Allure отчет: `tests-report/index.html`

## Очистка Docker окружения

```bash
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)
docker system prune -a --volumes -f
```
