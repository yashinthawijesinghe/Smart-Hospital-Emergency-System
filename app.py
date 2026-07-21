from flask import Flask, render_template, request, redirect, url_for
from database import init_db, save_patient, save_diagnosis, get_all_patients

app = Flask(__name__)

fired_log = []

def run_expert_system(facts):
    global fired_log
    fired_log = []

    def log(rule_id):
        fired_log.append(rule_id)

    def R1(f):
        if f.get("heart_rate",0)>150 and f.get("blood_pressure",999)<80 and "patient_status" not in f:
            f["patient_status"]="critical"; log("R1"); return True

    def R2(f):
        if f.get("oxygen_saturation",100)<85 and "respiratory_failure" not in f:
            f["respiratory_failure"]=True; log("R2"); return True

    def R3(f):
        if f.get("temperature",0)>40 and f.get("consciousness")=="unresponsive" and "septic_shock_risk" not in f:
            f["septic_shock_risk"]="high"; log("R3"); return True

    def R4(f):
        if f.get("chest_pain") and f.get("sweating") and f.get("left_arm_pain") and "cardiac_event_suspected" not in f:
            f["cardiac_event_suspected"]=True; log("R4"); return True

    def R5(f):
        if f.get("bleeding")=="severe" and f.get("blood_pressure",999)<90 and "hemorrhagic_shock" not in f:
            f["hemorrhagic_shock"]=True; log("R5"); return True

    def R6(f):
        if f.get("facial_drooping") and f.get("speech_slurred") and f.get("arm_weakness") and "stroke_suspected" not in f:
            f["stroke_suspected"]=True; log("R6"); return True

    def R7(f):
        if f.get("trauma") and f.get("mechanism")=="high_impact" and "internal_injury_risk" not in f:
            f["internal_injury_risk"]="high"; log("R7"); return True

    def R8(f):
        if f.get("cardiac_event_suspected") and "recommend_ECG" not in f:
            f["recommend_ECG"]=True; log("R8"); return True

    def R9(f):
        if f.get("stroke_suspected") and "recommend_CT" not in f:
            f["recommend_CT"]=True
            if f.get("has_allergy") and f.get("allergy_drug")=="tPA":
                f["tPA_blocked"]=True
            else:
                f["administer_tPA"]=True
            log("R9"); return True

    def R10(f):
        if f.get("hemorrhagic_shock") and "recommend_blood_transfusion" not in f:
            f["recommend_blood_transfusion"]=True; log("R10"); return True

    def R11(f):
        if f.get("respiratory_failure") and "recommend_intubation" not in f:
            f["recommend_intubation"]=True; log("R11"); return True

    def R12(f):
        if f.get("patient_status")=="critical" and f.get("icu_available") and "recommend_ICU" not in f:
            f["recommend_ICU"]=True; log("R12"); return True

    def R13(f):
        if f.get("patient_status")=="critical" and "alert_level" not in f:
            f["alert_level"]="RED"; f["notify_senior_doctor"]=True; log("R13"); return True

    def R14(f):
        if f.get("age",99)<12 and f.get("patient_status")=="critical" and "notify_pediatric" not in f:
            f["notify_pediatric"]=True; log("R14"); return True

    def R15(f):
        if f.get("has_allergy") and f.get("administer_tPA") and f.get("allergy_drug")=="tPA" and "allergy_flagged" not in f:
            f["administer_tPA"]=False; f["allergy_flagged"]=True; log("R15"); return True

    def R16(f):
        if f.get("patient_status")=="critical" and not f.get("icu_available") and "emergency_transfer" not in f:
            f["emergency_transfer"]=True; log("R16"); return True

    def R17(f):
        if f.get("multiple_symptoms") and "vitals_first" not in f:
            f["vitals_first"]=True; log("R17"); return True

    def R18(f):
        if f.get("patient_status")=="critical" and "skip_triage" not in f:
            f["skip_triage"]=True; log("R18"); return True

    rules = [R17, R18, R13, R14, R15, R16,
             R1, R2, R3, R4, R5, R6, R7,
             R8, R9, R10, R11, R12]

    cycle = 0
    while True:
        fired = False
        for rule in rules:
            if rule(facts):
                fired = True
        if not fired:
            break
        cycle += 1
        if cycle > 20:
            break

    if "alert_level" not in facts:
        facts["alert_level"] = "GREEN"
    if "patient_status" not in facts:
        facts["patient_status"] = "stable"

    return facts, fired_log


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    form = request.form

    patient_data = {
        "name":              form.get("name", "Unknown"),
        "age":               int(form.get("age", 30)),
        "gender":            form.get("gender", "male"),
        "heart_rate":        int(form.get("heart_rate", 80)),
        "blood_pressure":    int(form.get("blood_pressure", 120)),
        "oxygen_saturation": int(form.get("oxygen_saturation", 98)),
        "temperature":       float(form.get("temperature", 37)),
        "consciousness":     form.get("consciousness", "responsive"),
        "chest_pain":        1 if form.get("chest_pain") else 0,
        "sweating":          1 if form.get("sweating") else 0,
        "left_arm_pain":     1 if form.get("left_arm_pain") else 0,
        "bleeding":          form.get("bleeding", "none"),
        "facial_drooping":   1 if form.get("facial_drooping") else 0,
        "speech_slurred":    1 if form.get("speech_slurred") else 0,
        "arm_weakness":      1 if form.get("arm_weakness") else 0,
        "trauma":            1 if form.get("trauma") else 0,
        "has_allergy":       1 if form.get("has_allergy") else 0,
        "allergy_drug":      form.get("allergy_drug", ""),
        "icu_available":     1 if form.get("icu_available") else 0,
    }

    facts = {
        "heart_rate":        patient_data["heart_rate"],
        "blood_pressure":    patient_data["blood_pressure"],
        "oxygen_saturation": patient_data["oxygen_saturation"],
        "temperature":       patient_data["temperature"],
        "consciousness":     patient_data["consciousness"],
        "chest_pain":        bool(patient_data["chest_pain"]),
        "sweating":          bool(patient_data["sweating"]),
        "left_arm_pain":     bool(patient_data["left_arm_pain"]),
        "bleeding":          patient_data["bleeding"],
        "facial_drooping":   bool(patient_data["facial_drooping"]),
        "speech_slurred":    bool(patient_data["speech_slurred"]),
        "arm_weakness":      bool(patient_data["arm_weakness"]),
        "trauma":            bool(patient_data["trauma"]),
        "has_allergy":       bool(patient_data["has_allergy"]),
        "allergy_drug":      patient_data["allergy_drug"],
        "icu_available":     bool(patient_data["icu_available"]),
        "age":               patient_data["age"],
        "gender":            patient_data["gender"],
        "multiple_symptoms": True,
    }

    facts, rules_fired = run_expert_system(facts)
    patient_id = save_patient(patient_data)
    save_diagnosis(patient_id, facts, rules_fired)

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    patients = get_all_patients()
    return render_template("dashboard.html", patients=patients)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)