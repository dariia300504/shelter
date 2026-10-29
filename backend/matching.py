"""Модуль підбору: нормалізація, жорсткі критерії, оцінювання,
ранжування та формування пояснень."""
from datetime import date

PRIORITY_BONUS = 0.05      # бонус пріоритету (підрозділ 3.10)
SIZE_RANK = {"small": 0, "medium": 1, "large": 2}
MAX_STAY_DAYS = 180        # термін, після якого оцінка дорівнює 1


# ---------- Нормалізація часткових оцінок (підрозділ 3.10) ----------

def species_score(profile, animal):
    if animal["species"] == profile["preferred_species"]:
        return 1.0
    if animal["species"] == profile.get("allowed_species"):
        return 0.5
    return 0.0


def activity_score(profile, animal):
    # лінгвістична шкала: 0,1 ... 0,9 (таблиця 3.5)
    diff = abs(float(profile["activity_level"])
               - float(animal["activity_level"]))
    return round(max(0.0, 1.0 - diff), 2)


def experience_score(profile, animal):
    gap = animal["required_exp"] - profile["experience"]
    return 1.0 if gap <= 0 else max(0.0, 1.0 - 0.5 * gap)


def time_score(profile, animal):
    need = float(animal["care_time"])
    have = float(profile["time_per_day"])
    return 1.0 if need <= 0 else round(min(1.0, have / need), 2)


def age_score(profile, animal):
    # трикутна функція належності до бажаного вікового діапазону
    lo, hi = profile["age_min_months"], profile["age_max_months"]
    age = animal["age_months"]
    if age < lo or age > hi:
        return 0.0
    mid, half = (lo + hi) / 2, (hi - lo) / 2 or 1
    return round(1.0 - 0.5 * abs(age - mid) / half, 2)


def stay_score(animal, today=None):
    today = today or date.today()
    days = (today - animal["intake_date"]).days
    return round(min(1.0, days / MAX_STAY_DAYS), 2)


def partial_scores(profile, animal, today=None):
    return {
        "species": species_score(profile, animal),
        "activity": activity_score(profile, animal),
        "exp": experience_score(profile, animal),
        "time": time_score(profile, animal),
        "age": age_score(profile, animal),
        "stay": stay_score(animal, today),
    }


# ---------- Жорсткі критерії (підрозділ 3.5) ----------

def passes_hard_filters(profile, animal):
    if animal["status"] != "available":
        return False
    if profile["has_children"] and not animal["child_friendly"]:
        return False
    if profile["has_pets"] and not animal["pet_friendly"]:
        return False
    if animal["size"] == "large" and not profile["suitable_for_large"]:
        return False
    return True


# ---------- Зважене оцінювання ----------

def score_animal(partial, weights, is_priority):
    contributions = {c: weights[c] * partial[c] for c in weights}
    base = sum(contributions.values())
    total = min(1.0, base + (PRIORITY_BONUS if is_priority else 0.0))
    top = sorted(contributions, key=contributions.get, reverse=True)[:3]
    return round(total, 3), top


# ---------- Формування пояснень ----------

def phrase(code, value):
    if code == "species":
        return ("повна відповідність бажаному виду" if value == 1.0
                else "допустимий вид тварини")
    if code == "activity":
        return ("дуже близький рівень активності" if value >= 0.9
                else "підходящий рівень активності")
    return {
        "exp": "достатній досвід для догляду",
        "time": "догляд вкладається у ваш вільний час",
        "age": "підходящий вік",
        "stay": "тварина довго чекає на дім",
    }[code]


def explain(top, partial, is_priority):
    parts = [phrase(c, partial[c]) for c in top]
    text = ", ".join(parts[:-1]) + " та " + parts[-1]
    if is_priority:
        text += "; тварина евакуйована і потребує невідкладного влаштування"
    return text[0].upper() + text[1:]


# ---------- Повний цикл підбору ----------

def recommend(profile, animals, weights, partial=None, top_n=10,
              today=None):
    """Повертає Top-N тварин із балом і поясненням.
    partial — готові часткові оцінки {animal_id: {...}}; якщо не задано,
    їх обчислює функція partial_scores()."""
    result = []
    for a in animals:
        if not passes_hard_filters(profile, a):
            continue
        p = (partial[a["animal_id"]] if partial
             else partial_scores(profile, a, today))
        total, top = score_animal(p, weights, a["priority_status"])
        result.append({
            "animal_id": a["animal_id"],
            "name": a["name"],
            "score": total,
            "priority": a["priority_status"],
            "explanation": explain(top, p, a["priority_status"]),
        })
    result.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(result[:top_n], start=1):
        r["rank"] = i
    return result[:top_n]
