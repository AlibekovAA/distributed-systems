# Проект
Этот проект представляет собой распределенную систему с микросервисной архитектурой.

## Общая архитектура системы
```mermaid
graph TD
    Client["Клиентское приложение"] --> Frontend["Frontend"]

    subgraph Основные["Основные сервисы"]
        Frontend --> Auth["Auth Service"]
        Frontend --> Products["Product Catalog"]
        Frontend --> Rec["Recommendation Service"]
        Products -->|"user.id"| RMQ[("RabbitMQ")]
        RMQ -->|"user.id"| Rec
        Rec -->|"recommendation"| RMQ
        RMQ -->|"recommendation"| Products
    end

    subgraph Мониторинг["Система мониторинга"]
        Auth --> Prometheus["Prometheus"]
        Products --> Prometheus
        Prometheus --> Grafana["Grafana"]
    end

    Auth --> DB["База данных"]
    Products --> DB["База данных"]
    Rec --> DB["База данных"]

    classDef client fill:#90CAF9,stroke:#1976D2,color:#000
    classDef frontend fill:#81C784,stroke:#388E3C,color:#000
    classDef service fill:#FFB74D,stroke:#F57C00,color:#000
    classDef monitor fill:#CE93D8,stroke:#7B1FA2,color:#000
    classDef database fill:#B39DDB,stroke:#512DA8,color:#000
    classDef rabbit fill:#FFA500,stroke:#FF8C00,color:#000

    class Client client
    class Frontend frontend
    class Auth,Products,Rec service
    class Prometheus,Grafana monitor
    class DBAuth,DBProducts,DBRec database
    class RMQ rabbit
```

## Запуск проекта
Для запуска проекта необходимо выполнить следующие шаги:

### 1. Docker Compose
Запустите Docker Compose командой:
```bash
docker-compose up --build
```

### 2. Доступные сервисы
После успешного запуска будут доступны следующие сервисы:

#### Frontend
[http://localhost:3000](http://localhost:3000)

#### Auth Service API
[http://localhost:8000/auth](http://localhost:8000/auth)

#### PgAdmin
[http://localhost:5050](http://localhost:5050)

#### Product Catalog Service
[http://localhost:8080](http://localhost:8080)

#### Мониторинг
- Prometheus: [http://localhost:9090](http://localhost:9090)
- Grafana: [http://localhost:4000](http://localhost:4000)
* Предустановленные дашборды:
  - Auth Service Dashboard
  - Product Catalog Service Dashboard

## Система рекомендаций
Сервис предоставляет персонализированные рекомендации товаров.

### Архитектура системы рекомендаций
```mermaid
graph TD
A["Предпочтения пользователя"] --> B["Анализ предпочтений"]
C["Коллаборативная фильтрация"] --> D["Матрица взаимодействий"]
B --> E["Финальные рекомендации"]
D --> E
F["Наличие товаров"] --> E

style A fill:#f9f,stroke:#333,color:#000
style C fill:#bbf,stroke:#333,color:#000
style F fill:#bfb,stroke:#333,color:#000
```

### Алгоритм работы
#### 1. Анализ предпочтений пользователя
- Учет заполненной анкеты по категориям
- Расчет максимального балла соответствия товара
- Влияние на финальный результат: 70%

#### 2. Коллаборативная фильтрация
- Построение матрицы взаимодействий пользователь-товар
- Поиск похожих пользователей через косинусное сходство
- Анализ покупок похожих пользователей
- Нормализация коллаборативных оценок
- Влияние на финальный результат: 30%

## Frontend
Основные компоненты фронтенд части:

### Функциональность
- Регистрация и вход в систему
- Личный кабинет пользователя
- Навигация по разделам:
  * Профиль пользователя
  * Каталог товаров
  * Корзина покупок

## Auth Service API
Основные эндпоинты:

### Аутентификация
```markdown
POST /auth/register    - регистрация
POST /auth/login      - вход
GET /auth/profile     - профиль пользователя
POST /auth/change-password - смена пароля
POST /auth/add-balance    - пополнение баланса
POST /auth/token/refresh  - обновление токена
GET /preferences/check    - проверка анкеты предпочтений
POST /preferences/save    - сохранение предпочтений
```

### Здоровье сервиса
```markdown
GET /auth/health      - проверка состояния
GET /auth/metrics     - возвращает сервисную информацию
```

## Product Catalog Service API
Основные эндпоинты:

### Товары
```markdown
GET /products/{email}   - список товаров
POST /products         - создание товара
DELETE /products       - удаление товара
```

### Заказы
```markdown
GET /order/{email}     - корзина пользователя
POST /order/add       - добавление в корзину
DELETE /order/{email}/{product_id} - удаление из корзины
POST /order/{email}/pay    - оплата заказа
GET /orders/{email}/history - история заказов
POST /order/{email}/clear  - очистка корзины
```

## Swagger документация
Для просмотра документации необходимо:
```bash
cd swagger
python swagger.py
```
Документация доступна по адресу:
[http://petstore.swagger.io/?url=http://localhost:4040/combined-swagger.json](http://petstore.swagger.io/?url=http://localhost:4040/combined-swagger.json)

# Структура базы данных
## Таблица пользователей (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    hashed_password TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    balance BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Таблица товаров (product)
```sql
CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price BIGINT NOT NULL,
    quantity INTEGER NOT NULL
);
```

## Таблица заказов (order)
```sql
CREATE TABLE "order" (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) REFERENCES users(email) ON DELETE CASCADE,
    product_id INTEGER REFERENCES product(id) ON DELETE CASCADE
);
```

## Таблица предпочтений пользователей (user_preferences)
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    preference_name VARCHAR(255) NOT NULL,
    preference_value VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Таблица истории (history)
```sql
CREATE TABLE "history" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES product(id) ON DELETE CASCADE,
    order_number INTEGER
);
```

## Таблица категорий (categories)
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);
```

## Таблица связи товаров и категорий (product_categories)
```sql
CREATE TABLE product_categories (
    product_id INTEGER REFERENCES product(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, category_id)
);
```

## Взаимосвязи между таблицами
```mermaid
graph TD
    subgraph Основные["Основные таблицы"]
        U[Пользователи] --> UP[Предпочтения]
        U --> O[Заказы]
        U --> H[История]
        P[Товары] --> O
        P --> PC[Товары-Категории]
        PC --> C[Категории]
    end

    subgraph Связи["Типы связей"]
        R1[ON DELETE CASCADE]
        R2[UNIQUE]
    end

    U --> R1
    C --> R2
    P --> R2

    classDef users fill:#90CAF9,stroke:#1976D2,color:#000
    classDef products fill:#81C784,stroke:#388E3C,color:#000
    classDef categories fill:#FFB74D,stroke:#F57C00,color:#000
    classDef orders fill:#CE93D8,stroke:#7B1FA2,color:#000

    class U,UP users
    class P,PC products
    class C categories
    class O,H orders
```

## Разработка
### Frontend
- Исходный код находится в `frontend/src/`
- Модули разделены по папкам в `src/modules/`
- Общие стили в `src/styles/common/`
- Сервисы для работы с API в `src/services/`
- Утилиты и вспомогательные функции в `src/utils/`

### Backend
#### Auth Service
- Расположен в `backend/auth-service/`
- Модульная структура:
  * `app/` - основной код приложения
  * `models/` - модели данных
  * `services/` - бизнес-логика
  * `tests/` - тесты

#### Recommendation Service
- Расположен в `backend/recommendation-service/`
- Модульная структура:
  * `app/` - основной код приложения
  * `models/` - модели данных

#### Product Catalog Service
- Расположен в `backend/product-catalog-service/`
- Модульная структура:
  * `src/application/` - обработчики HTTP запросов
  * `src/config/` - конфигурация приложения
  * `src/db/` - работа с базой данных
  * `src/models/` - модели данных
  * `src/docs/` - Swagger документация

## Тестирование
### Запуск тестов
```bash
cd tests
python run_tests.py
```

### Просмотр отчетов
Открыть файл `allure-report/index.html`
![Allure](tests/allure.jpg)

## Очистка Docker окружения
```bash
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)
docker system prune -a --volumes -f
```
