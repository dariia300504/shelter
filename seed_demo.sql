-- Демонстраційні дані для ручної перевірки API (не входять до додатків роботи)
INSERT INTO users (name, contact, password_hash)
VALUES ('Тестовий користувач', 'test@example.com', 'demo');

INSERT INTO shelters (name, address)
VALUES ('Теплий кут', 'Львів');

INSERT INTO animals (shelter_id, name, species, age_months, size, activity_level,
                     required_exp, care_time, child_friendly, pet_friendly,
                     intake_date, priority_status)
VALUES
 (1, 'Барсик', 'собака', 36, 'small',  0.3, 1, 2.5, TRUE, TRUE, current_date - 162, TRUE),
 (1, 'Луна',   'собака', 30, 'medium', 0.5, 1, 2.0, TRUE, TRUE, current_date - 126, FALSE),
 (1, 'Рекс',   'собака', 24, 'large',  0.7, 1, 3.0, TRUE, TRUE, current_date - 50,  TRUE),
 (1, 'Боня',   'кіт',    20, 'small',  0.9, 2, 3.0, TRUE, TRUE, current_date - 144, FALSE);
