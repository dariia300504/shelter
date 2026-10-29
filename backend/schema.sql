-- Схема бази даних системи підбору тварин (PostgreSQL 16)

CREATE TYPE user_role AS ENUM ('owner', 'staff', 'admin');
CREATE TYPE animal_size AS ENUM ('small', 'medium', 'large');
CREATE TYPE animal_status AS ENUM ('available', 'booked',
                                   'adopted', 'archived');

CREATE TABLE users (
    user_id        SERIAL PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    contact        VARCHAR(100) NOT NULL UNIQUE,
    role           user_role NOT NULL DEFAULT 'owner',
    password_hash  VARCHAR(255) NOT NULL
);

CREATE TABLE shelters (
    shelter_id  SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    address     VARCHAR(255) NOT NULL,
    contacts    VARCHAR(150)
);

CREATE TABLE questionnaires (
    questionnaire_id   SERIAL PRIMARY KEY,
    user_id            INT NOT NULL REFERENCES users(user_id)
                           ON DELETE CASCADE,
    housing_type       VARCHAR(30) NOT NULL,
    suitable_for_large BOOLEAN NOT NULL DEFAULT FALSE,
    experience         SMALLINT NOT NULL CHECK (experience BETWEEN 0 AND 2),
    has_children       BOOLEAN NOT NULL,
    has_pets           BOOLEAN NOT NULL,
    allergies          BOOLEAN NOT NULL DEFAULT FALSE,
    preferred_species  VARCHAR(30) NOT NULL,
    allowed_species    VARCHAR(30),
    preferred_size     animal_size,
    age_min_months     INT NOT NULL DEFAULT 0,
    age_max_months     INT NOT NULL DEFAULT 240,
    activity_level     NUMERIC(2,1) CHECK (activity_level BETWEEN 0 AND 1),
    time_per_day       NUMERIC(3,1) NOT NULL,
    created_at         TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE animals (
    animal_id        SERIAL PRIMARY KEY,
    shelter_id       INT NOT NULL REFERENCES shelters(shelter_id),
    name             VARCHAR(50) NOT NULL,
    species          VARCHAR(30) NOT NULL,
    breed            VARCHAR(50),
    age_months       INT NOT NULL CHECK (age_months >= 0),
    size             animal_size NOT NULL,
    temperament      VARCHAR(200),
    activity_level   NUMERIC(2,1) CHECK (activity_level BETWEEN 0 AND 1),
    required_exp     SMALLINT NOT NULL DEFAULT 0,
    care_time        NUMERIC(3,1) NOT NULL DEFAULT 1,
    health_status    VARCHAR(200),
    child_friendly   BOOLEAN NOT NULL DEFAULT FALSE,
    pet_friendly     BOOLEAN NOT NULL DEFAULT FALSE,
    intake_date      DATE NOT NULL,
    priority_status  BOOLEAN NOT NULL DEFAULT FALSE,
    status           animal_status NOT NULL DEFAULT 'available'
);

CREATE TABLE criteria (
    criterion_id    SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL,
    scale_type      VARCHAR(30) NOT NULL,
    weight          NUMERIC(3,2) NOT NULL CHECK (weight BETWEEN 0 AND 1),
    is_hard_filter  BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE matches (
    match_id          SERIAL PRIMARY KEY,
    questionnaire_id  INT NOT NULL REFERENCES questionnaires
                          ON DELETE CASCADE,
    animal_id         INT NOT NULL REFERENCES animals(animal_id),
    score             NUMERIC(4,3) NOT NULL,
    rank              INT NOT NULL,
    explanation       TEXT,
    created_at        TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE match_criteria (
    match_id      INT REFERENCES matches(match_id) ON DELETE CASCADE,
    criterion_id  INT REFERENCES criteria(criterion_id),
    weight_used   NUMERIC(3,2) NOT NULL,
    PRIMARY KEY (match_id, criterion_id)
);

CREATE INDEX idx_animals_status ON animals(status);
CREATE INDEX idx_matches_questionnaire ON matches(questionnaire_id);

-- Початкові вагові коефіцієнти м'яких критеріїв (таблиця 3.2)
INSERT INTO criteria (code, name, scale_type, weight) VALUES
  ('species',  'Вид та порода тварини',           'номінальна',    0.20),
  ('activity', 'Рівень активності / темперамент', 'лінгвістична', 0.20),
  ('exp',      'Відповідний досвід утримання',    'порядкова',    0.15),
  ('time',     'Час на догляд',                   'кількісна',    0.15),
  ('age',      'Вік тварини',                     'кількісна',    0.15),
  ('stay',     'Термін перебування в притулку',   'кількісна',    0.15);

-- Жорсткі критерії (вага не використовується)
INSERT INTO criteria (code, name, scale_type, weight, is_hard_filter)
VALUES
  ('children', 'Сумісність з дітьми',          'бінарна', 0, TRUE),
  ('pets',     'Сумісність з іншими тваринами', 'бінарна', 0, TRUE),
  ('housing',  'Відповідність житловим умовам', 'бінарна', 0, TRUE);
