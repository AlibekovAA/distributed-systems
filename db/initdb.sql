CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  hashed_password TEXT  NOT NULL,
  name VARCHAR(255)  NOT NULL,
  balance BIGINT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE product (
  id SERIAL PRIMARY KEY, 
  name VARCHAR(255) NOT NULL, 
  description TEXT,
  price BIGINT NOT NULL, 
  quantity INTEGER NOT NULL
);


CREATE TABLE "order" (
  id SERIAL PRIMARY KEY, 
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, 
  product_id INTEGER REFERENCES product(id) ON DELETE CASCADE
);

CREATE TABLE "history" (
  id SERIAL PRIMARY KEY, 
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, 
  product_id INTEGER REFERENCES product(id) ON DELETE CASCADE,
  order_number INTEGER
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY, 
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE product_categories (
    product_id INTEGER REFERENCES product(id) ON DELETE CASCADE, 
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE, 
    PRIMARY KEY (product_id, category_id)
);



CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY, 
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, 
    product_id INTEGER REFERENCES product(id) ON DELETE CASCADE, 
    score INTEGER NOT NULL
);


INSERT INTO product (name, price, quantity, description)
VALUES
    ('Apple iPhone 14', 79900, 50, 'Последняя модель iPhone с дисплеем 6,1 дюйма, чипом A15 Bionic и системой с двумя камерами.'),
    ('Samsung Galaxy S23', 74900, 30, 'Флагманский смартфон от Samsung с 6,2-дюймовым экраном Dynamic AMOLED и процессором Snapdragon 8 Gen 2.'),
    ('Sony WH-1000XM5', 34900, 20, 'Наушники с лучшей в своем классе системой шумоподавления и временем работы до 30 часов.'),
    ('Dell XPS 13', 99900, 100, 'Компактный 13-дюймовый ноутбук с процессором Intel Core i7 и высококачественным 4K экраном с сенсорным управлением.'),
    ('Fitbit Charge 5', 17900, 50, 'Продвинутый фитнес-трекер с мониторингом сердечного ритма, GPS и цветным сенсорным экраном.'),
    ('Bose SoundLink Revolve+', 29900, 40, 'Портативная Bluetooth-колонка с объемным звуком на 360° и временем работы до 16 часов.'),
    ('Nike Air Max 270', 15000, 200, 'Модные кроссовки с большим амортизирующим элементом Max Air в пятке для комфортной ходьбы.'),
    ('Sony PlayStation 5', 49900, 15, 'Консоль нового поколения для игр в 4K с ультрабыстродействующим SSD и контроллером DualSense.');


INSERT INTO categories (name)
VALUES
    ('Смартфоны'),
    ('Наушники'),
    ('Ноутбуки'),
    ('Фитнес'),
    ('Колонки'),
    ('Кроссовки'),
    ('Игровые консоли');
