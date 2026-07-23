from dataclasses import dataclass
from typing import Callable

from flask import Flask, render_template, request, redirect, url_for

from database import get_all_patients, get_patient, init_db, save_diagnosis, save_patient


app = Flask(__name__)
init_db()


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    category: str
    priority: int
    confidence: float
    conditions: str
    conclusion: str
    matches: Callable[[dict], bool]
    apply: Callable[[dict], dict]

    @property
    def specificity(self):
        return self.conditions.count(" AND ") + 1


def missing(facts, key):
    return key not in facts


RULES = [
    Rule("R1", "Circulatory collapse", "Relation", 100, .98,
         "heart rate > 150 AND blood pressure < 80", "patient is critical",
         lambda f: f["heart_rate"] > 150 and f["blood_pressure"] < 80 and missing(f, "patient_status"),
         lambda f: {"patient_status": "critical", "circulatory_collapse": True}),
    Rule("R2", "Respiratory failure", "Relation", 98, .97,
         "oxygen saturation < 85", "respiratory failure is suspected",
         lambda f: f["oxygen_saturation"] < 85 and missing(f, "respiratory_failure"),
         lambda f: {"respiratory_failure": True}),
    Rule("R3", "Septic shock risk", "Heuristic", 97, .94,
         "temperature > 40 AND patient is unresponsive", "septic shock risk is high",
         lambda f: f["temperature"] > 40 and f["consciousness"] == "unresponsive" and missing(f, "septic_shock_risk"),
         lambda f: {"septic_shock_risk": "high"}),
    Rule("R4", "Cardiac event pattern", "Relation", 93, .95,
         "chest pain AND sweating AND left-arm pain", "cardiac event is suspected",
         lambda f: f["chest_pain"] and f["sweating"] and f["left_arm_pain"] and missing(f, "cardiac_event_suspected"),
         lambda f: {"cardiac_event_suspected": True}),
    Rule("R5", "Hemorrhagic shock", "Relation", 99, .97,
         "severe bleeding AND blood pressure < 90", "hemorrhagic shock is suspected",
         lambda f: f["bleeding"] == "severe" and f["blood_pressure"] < 90 and missing(f, "hemorrhagic_shock"),
         lambda f: {"hemorrhagic_shock": True}),
    Rule("R6", "FAST stroke pattern", "Relation", 96, .96,
         "facial drooping AND slurred speech AND arm weakness", "stroke is suspected",
         lambda f: f["facial_drooping"] and f["speech_slurred"] and f["arm_weakness"] and missing(f, "stroke_suspected"),
         lambda f: {"stroke_suspected": True}),
    Rule("R7", "High-impact trauma", "Heuristic", 88, .88,
         "trauma AND mechanism is high impact", "internal injury risk is high",
         lambda f: f["trauma"] and f["mechanism"] == "high_impact" and missing(f, "internal_injury_risk"),
         lambda f: {"internal_injury_risk": "high"}),
    Rule("R8", "Cardiac investigation", "Recommendation", 78, .95,
         "cardiac event is suspected", "perform an immediate ECG",
         lambda f: f.get("cardiac_event_suspected") and missing(f, "recommend_ECG"),
         lambda f: {"recommend_ECG": True}),
    Rule("R9", "Stroke imaging", "Recommendation", 79, .96,
         "stroke is suspected", "perform an urgent CT scan",
         lambda f: f.get("stroke_suspected") and missing(f, "recommend_CT"),
         lambda f: {"recommend_CT": True}),
    Rule("R10", "Replace blood loss", "Recommendation", 84, .94,
         "hemorrhagic shock is suspected", "prepare a blood transfusion",
         lambda f: f.get("hemorrhagic_shock") and missing(f, "recommend_blood_transfusion"),
         lambda f: {"recommend_blood_transfusion": True}),
    Rule("R11", "Airway protection", "Directive", 86, .96,
         "respiratory failure is suspected", "prepare immediate intubation",
         lambda f: f.get("respiratory_failure") and missing(f, "recommend_intubation"),
         lambda f: {"recommend_intubation": True}),
    Rule("R12", "ICU admission", "Recommendation", 76, .92,
         "patient is critical AND ICU is available", "admit patient to ICU",
         lambda f: f.get("patient_status") == "critical" and f["icu_available"] and missing(f, "recommend_ICU"),
         lambda f: {"recommend_ICU": True}),
    Rule("R13", "Red alert escalation", "Directive", 90, .99,
         "patient is critical", "set RED alert and notify senior doctor",
         lambda f: f.get("patient_status") == "critical" and missing(f, "alert_level"),
         lambda f: {"alert_level": "RED", "notify_senior_doctor": True}),
    Rule("R14", "Pediatric escalation", "Directive", 85, .95,
         "age < 12 AND patient is critical", "notify pediatric specialist",
         lambda f: f["age"] < 12 and f.get("patient_status") == "critical" and missing(f, "notify_pediatric"),
         lambda f: {"notify_pediatric": True}),
    Rule("R15", "tPA allergy safety", "Directive", 101, .99,
         "stroke is suspected AND patient has tPA allergy", "block tPA administration",
         lambda f: f.get("stroke_suspected") and f["has_allergy"] and f["allergy_drug"].strip().lower() == "tpa" and missing(f, "tPA_blocked"),
         lambda f: {"tPA_blocked": True, "administer_tPA": False}),
    Rule("R16", "Unavailable ICU strategy", "Strategy", 89, .98,
         "patient is critical AND ICU is unavailable", "arrange emergency transfer",
         lambda f: f.get("patient_status") == "critical" and not f["icu_available"] and missing(f, "emergency_transfer"),
         lambda f: {"emergency_transfer": True}),
    Rule("R17", "Multiple-symptom strategy", "Strategy", 65, .85,
         "two or more symptoms are present", "record vital signs before routine history",
         lambda f: f["symptom_count"] >= 2 and missing(f, "vitals_first"),
         lambda f: {"vitals_first": True}),
    Rule("R18", "Critical triage bypass", "Directive", 87, .98,
         "patient is critical", "bypass the routine triage queue",
         lambda f: f.get("patient_status") == "critical" and missing(f, "skip_triage"),
         lambda f: {"skip_triage": True}),
    Rule("R19", "High fever", "Relation", 72, .90,
         "temperature >= 39", "serious infection is suspected",
         lambda f: f["temperature"] >= 39 and missing(f, "infection_risk"),
         lambda f: {"infection_risk": "high"}),
    Rule("R20", "Sepsis treatment", "Recommendation", 82, .91,
         "septic shock risk is high", "start sepsis protocol and urgent antibiotics",
         lambda f: f.get("septic_shock_risk") == "high" and missing(f, "recommend_sepsis_protocol"),
         lambda f: {"recommend_sepsis_protocol": True}),
    Rule("R21", "Hypothermia", "Relation", 73, .94,
         "temperature < 35", "hypothermia is suspected",
         lambda f: f["temperature"] < 35 and missing(f, "hypothermia"),
         lambda f: {"hypothermia": True}),
    Rule("R22", "Active warming", "Recommendation", 74, .93,
         "hypothermia is suspected", "begin active warming",
         lambda f: f.get("hypothermia") and missing(f, "recommend_warming"),
         lambda f: {"recommend_warming": True}),
    Rule("R23", "Life-threat escalation", "Strategy", 92, .96,
         "respiratory failure OR hemorrhagic shock OR septic shock risk", "patient is critical",
         lambda f: (f.get("respiratory_failure") or f.get("hemorrhagic_shock") or f.get("septic_shock_risk") == "high") and missing(f, "patient_status"),
         lambda f: {"patient_status": "critical"}),
    Rule("R24", "Multi-threat response", "Strategy", 95, .97,
         "two or more life threats are suspected", "activate emergency response team",
         lambda f: sum(bool(f.get(k)) for k in ("respiratory_failure", "hemorrhagic_shock", "cardiac_event_suspected", "stroke_suspected")) >= 2 and missing(f, "activate_emergency_team"),
         lambda f: {"activate_emergency_team": True}),
]


def rule_rank(rule):
    """Metarules: highest priority, then specificity, confidence, then rule ID."""
    return (-rule.priority, -rule.specificity, -rule.confidence, int(rule.id[1:]))


def run_expert_system(initial_facts):
    facts = dict(initial_facts)
    fired = []
    trace = []

    for cycle in range(1, len(RULES) + 1):
        conflict_set = [rule for rule in RULES if rule.id not in fired and rule.matches(facts)]
        if not conflict_set:
            break
        ranked = sorted(conflict_set, key=rule_rank)
        winner = ranked[0]
        new_facts = winner.apply(facts)
        facts.update(new_facts)
        fired.append(winner.id)
        trace.append({
            "cycle": cycle,
            "candidates": [rule.id for rule in ranked],
            "selected": winner.id,
            "reason": f"priority {winner.priority}, specificity {winner.specificity}, confidence {winner.confidence:.0%}",
            "added": new_facts,
        })

    facts.setdefault("alert_level", "GREEN")
    facts.setdefault("patient_status", "stable")
    return facts, fired, trace


def build_patient_data(form):
    return {
        "name": form.get("name", "Unknown").strip() or "Unknown",
        "age": int(form.get("age", 30)),
        "gender": form.get("gender", "male"),
        "heart_rate": int(form.get("heart_rate", 80)),
        "blood_pressure": int(form.get("blood_pressure", 120)),
        "oxygen_saturation": int(form.get("oxygen_saturation", 98)),
        "temperature": float(form.get("temperature", 37)),
        "consciousness": form.get("consciousness", "responsive"),
        "chest_pain": bool(form.get("chest_pain")),
        "sweating": bool(form.get("sweating")),
        "left_arm_pain": bool(form.get("left_arm_pain")),
        "bleeding": form.get("bleeding", "none"),
        "facial_drooping": bool(form.get("facial_drooping")),
        "speech_slurred": bool(form.get("speech_slurred")),
        "arm_weakness": bool(form.get("arm_weakness")),
        "trauma": bool(form.get("trauma")),
        "mechanism": form.get("mechanism", "none"),
        "has_allergy": bool(form.get("has_allergy")),
        "allergy_drug": form.get("allergy_drug", "").strip(),
        "icu_available": bool(form.get("icu_available")),
    }


def facts_from_patient(patient):
    facts = dict(patient)
    symptom_keys = ("chest_pain", "sweating", "left_arm_pain", "facial_drooping",
                    "speech_slurred", "arm_weakness", "trauma")
    facts["symptom_count"] = sum(bool(patient[key]) for key in symptom_keys)
    if patient["bleeding"] != "none":
        facts["symptom_count"] += 1
    return facts


@app.route("/")
def index():
    return render_template("index.html", rule_count=len(RULES))


@app.route("/submit", methods=["POST"])
def submit():
    patient = build_patient_data(request.form)
    facts, fired, trace = run_expert_system(facts_from_patient(patient))
    patient_id = save_patient(patient)
    save_diagnosis(patient_id, facts, fired, trace)
    return redirect(url_for("result", patient_id=patient_id))


@app.route("/result/<int:patient_id>")
def result(patient_id):
    patient = get_patient(patient_id)
    if patient is None:
        return render_template("not_found.html"), 404
    return render_template("result.html", patient=patient)


@app.route("/dashboard")
def dashboard():
    query = request.args.get("q", "").strip()
    selected_id = request.args.get("patient_id", type=int)
    patients = get_all_patients(query)
    return render_template("dashboard.html", patients=patients, query=query, selected_id=selected_id)


@app.route("/rules")
def rules():
    categories = sorted({rule.category for rule in RULES})
    return render_template("rules.html", rules=RULES, categories=categories)


if __name__ == "__main__":
    app.run(debug=True)
