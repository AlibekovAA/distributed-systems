CREATE TABLE IF NOT EXISTS user_order_counters (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  next_order_number BIGINT NOT NULL DEFAULT 1
);

INSERT INTO user_order_counters (user_id, next_order_number)
SELECT user_id, COALESCE(MAX(order_number), 0) + 1
FROM history
WHERE user_id IS NOT NULL
GROUP BY user_id
ON CONFLICT (user_id) DO UPDATE
SET next_order_number = GREATEST(
  user_order_counters.next_order_number,
  EXCLUDED.next_order_number
);

CREATE INDEX IF NOT EXISTS idx_order_email ON "order" (email);
CREATE INDEX IF NOT EXISTS idx_history_user_order ON history (user_id, order_number);
CREATE INDEX IF NOT EXISTS idx_history_product_id ON history (product_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences (user_id);
