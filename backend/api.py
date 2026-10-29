"""API-сервер системи підбору тварин (FastAPI + PostgreSQL)."""
import os
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import matching

DSN = os.getenv("DATABASE_URL",
                "postgresql://app:app@localhost/pets")
app = FastAPI(title="Підбір тварини з притулку")


def db():
    return psycopg.connect(DSN, row_factory=dict_row)


class Questionnaire(BaseModel):
    user_id: int
    housing_type: str
    suitable_for_large: bool = False
    experience: int = Field(ge=0, le=2)
    has_children: bool
    has_pets: bool
    allergies: bool = False
    preferred_species: str
    allowed_species: str | None = None
    preferred_size: str | None = None
    age_min_months: int = Field(ge=0, default=0)
    age_max_months: int = Field(ge=0, default=240)
    activity_level: float = Field(ge=0, le=1)
    time_per_day: float = Field(gt=0)


class CriterionWeight(BaseModel):
    code: str
    weight: float = Field(ge=0, le=1)


@app.post("/questionnaire")
def create_questionnaire(q: Questionnaire):
    fields = q.model_dump()
    cols = ", ".join(fields)
    vals = ", ".join(f"%({k})s" for k in fields)
    with db() as conn:
        row = conn.execute(
            f"INSERT INTO questionnaires ({cols}) VALUES ({vals}) "
            "RETURNING questionnaire_id", fields).fetchone()
    return {"questionnaire_id": row["questionnaire_id"]}


@app.get("/recommendations")
def get_recommendations(questionnaire_id: int, top: int = 10):
    with db() as conn:
        profile = conn.execute(
            "SELECT * FROM questionnaires WHERE questionnaire_id = %s",
            (questionnaire_id,)).fetchone()
        if profile is None:
            raise HTTPException(404, "Анкету не знайдено")
        animals = conn.execute(
            "SELECT * FROM animals WHERE status = 'available'").fetchall()
        crit = conn.execute(
            "SELECT criterion_id, code, weight FROM criteria "
            "WHERE NOT is_hard_filter").fetchall()
        weights = {c["code"]: float(c["weight"]) for c in crit}

        result = matching.recommend(profile, animals, weights, top_n=top)
        if not result:
            return {"items": [],
                    "message": "Відповідних тварин не знайдено. "
                               "Спробуйте змінити анкету."}

        for r in result:
            m = conn.execute(
                "INSERT INTO matches (questionnaire_id, animal_id, score, "
                "rank, explanation) VALUES (%s, %s, %s, %s, %s) "
                "RETURNING match_id",
                (questionnaire_id, r["animal_id"], r["score"], r["rank"],
                 r["explanation"])).fetchone()
            for c in crit:
                conn.execute(
                    "INSERT INTO match_criteria VALUES (%s, %s, %s)",
                    (m["match_id"], c["criterion_id"], c["weight"]))
    return {"items": result}


@app.post("/appointments")
def book_visit(animal_id: int):
    with db() as conn:
        row = conn.execute(
            "UPDATE animals SET status = 'booked' WHERE animal_id = %s "
            "AND status = 'available' RETURNING animal_id",
            (animal_id,)).fetchone()
    if row is None:
        raise HTTPException(409, "Тварина вже недоступна для запису")
    return {"animal_id": animal_id, "status": "booked"}


@app.put("/admin/criteria")
def update_weights(items: list[CriterionWeight]):
    total = sum(i.weight for i in items)
    if abs(total - 1.0) > 1e-6:
        raise HTTPException(422, "Сума ваг має дорівнювати 1")
    with db() as conn:
        for i in items:
            conn.execute(
                "UPDATE criteria SET weight = %s WHERE code = %s "
                "AND NOT is_hard_filter", (i.weight, i.code))
    return {"updated": len(items)}
