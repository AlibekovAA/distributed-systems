CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  hashed_password TEXT  NOT NULL,
  name VARCHAR(255)  NOT NULL,
  balance BIGINT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
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
  email VARCHAR(255) REFERENCES users(email) ON DELETE CASCADE,
  product_id INTEGER REFERENCES product(id) ON DELETE CASCADE
);


CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    preference_name VARCHAR(255) NOT NULL,
    preference_value VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
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


INSERT INTO product (name, price, quantity, description)
VALUES
  ('Apple iPhone 14', 79900, 50, 'Latest iPhone model with 6.1-inch display, A15 Bionic chip, and dual-camera system.'),
  ('Samsung Galaxy S23', 74900, 30, 'Flagship Samsung smartphone with 6.2-inch Dynamic AMOLED display and Snapdragon 8 Gen 2 processor.'),
  ('Sony WH-1000XM5', 34900, 20, 'Headphones with best-in-class noise cancellation and up to 30 hours of battery life.'),
  ('Dell XPS 13', 99900, 100, 'Compact 13-inch laptop with Intel Core i7 processor and high-quality 4K touchscreen display.'),
  ('Fitbit Charge 5', 17900, 50, 'Advanced fitness tracker with heart rate monitoring, GPS, and color touchscreen.'),
  ('Bose SoundLink Revolve+', 29900, 40, 'Portable Bluetooth speaker with 360° sound and up to 16 hours of battery life.'),
  ('Nike Air Max 270', 15000, 200, 'Stylish sneakers with large Max Air cushioning unit in the heel for comfortable walking.'),
  ('Sony PlayStation 5', 49900, 15, 'Next-gen gaming console for 4K gaming with ultra-fast SSD and DualSense controller.'),
  ('MacBook Pro 16', 250000, 20, 'Professional Apple laptop with M2 Max processor and Mini-LED display.'),
  ('Xiaomi Redmi Note 12', 29900, 80, 'Affordable smartphone with 120Hz AMOLED display and 50MP camera.'),
  ('JBL Charge 5', 18900, 60, 'Waterproof portable speaker with powerful bass and 20-hour battery life.'),
  ('Garmin Fenix 7', 75000, 25, 'Premium sports smartwatch with GPS, heart rate sensor, and 18-day battery life.'),
  ('Asus ROG Zephyrus G14', 140000, 30, 'Gaming laptop with Ryzen 9 processor and RTX 4060 graphics card.'),
  ('Microsoft Xbox Series X', 59900, 25, 'Gaming console with 12 teraflops GPU and 4K 120FPS support.'),
  ('Adidas Ultraboost 22', 17000, 150, 'Running shoes with Boost cushioning and breathable Primeknit upper.'),
  ('Apple Watch Series 8', 45900, 40, 'Smartwatch with advanced health features and always-on display.'),
  ('Samsung Galaxy Watch 5', 39900, 35, 'Premium smartwatch with comprehensive health tracking and long battery life.'),
  ('AirPods Pro 2', 29900, 45, 'Wireless earbuds with active noise cancellation and spatial audio.'),
  ('Lenovo ThinkPad X1 Carbon', 159900, 25, 'Business laptop with Intel Core i7 and 14-inch display.'),
  ('Nintendo Switch OLED', 39900, 30, 'Gaming console with 7-inch OLED screen and detachable controllers.'),
  ('Puma RS-X', 12000, 100, 'Retro-style sneakers with chunky design and comfortable cushioning.'),
  ('Sony WF-1000XM4', 19900, 30, 'True wireless earbuds with industry-leading noise cancellation.'),
  ('Razer Blade 15', 189900, 20, 'Gaming laptop with RTX 4070 and 15.6-inch QHD display.'),
  ('Apple iPad Pro 12.9', 129900, 25, 'Pro tablet with M2 chip and Liquid Retina XDR display.'),
  ('DJI Mini 3 Pro', 99900, 15, 'Compact drone with 4K camera and advanced flight features.');


INSERT INTO categories (name)
VALUES
    ('Smartphones'),
    ('Headphones'),
    ('Laptops'),
    ('Fitness'),
    ('Loudspeakers'),
    ('Sneakers'),
    ('Gaming Consoles'),
    ('Smartwatches'),
    ('Accessories');


INSERT INTO product_categories (product_id, category_id)
VALUES
    (1, 1),
    (2, 1),
    (3, 2),
    (4, 3),
    (5, 4),
    (5, 9),
    (6, 5),
    (7, 6),
    (7, 4),
    (8, 7),
    (9, 3),
    (10, 1),
    (11, 5),
    (12, 8),
    (12, 4),
    (13, 3),
    (14, 7),
    (15, 6),
    (15, 4),
    (16, 8),
    (16, 4),
    (17, 8),
    (17, 4),
    (18, 2),
    (18, 9),
    (19, 3),
    (20, 7),
    (21, 6),
    (21, 4),
    (22, 2),
    (22, 9),
    (23, 3),
    (24, 9),
    (25, 9);
