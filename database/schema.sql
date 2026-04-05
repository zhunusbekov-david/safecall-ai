-- Таблица для жалоб на мошенников
CREATE TABLE IF NOT EXISTS fraud_reports (
    id SERIAL PRIMARY KEY,
    phone TEXT NOT NULL,
    city TEXT NOT NULL,
    text TEXT NOT NULL,
    risk_score FLOAT DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индекс для быстрого поиска по номеру
CREATE INDEX IF NOT EXISTS idx_fraud_reports_phone ON fraud_reports(phone);

-- Индекс для поиска по городу
CREATE INDEX IF NOT EXISTS idx_fraud_reports_city ON fraud_reports(city);

-- Пример данных для тестирования (опционально)
INSERT INTO fraud_reports (phone, city, text, risk_score) VALUES
('87001234567', 'Алматы', 'Представлялся сотрудником банка, просил данные карты', 0.95),
('87007654321', 'Астана', 'Говорил о выигрыше в лотерею, просил оплатить налог', 0.9),
('87005555555', 'Караганда', 'Предлагал лечение, требовал предоплату', 0.85)
ON CONFLICT DO NOTHING;


