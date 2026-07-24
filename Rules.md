# EmergencyLens Knowledge Base: Rules R1-R24

This document describes the complete rule base used by the Smart Hospital Emergency Expert System. It explains the inputs accepted by the system, the facts stored in working memory, the conditions that make each rule applicable, the facts produced when a rule fires, and the forward-chaining relationships between rules.

> **Educational warning:** The thresholds and recommendations in this project are designed to demonstrate rule-based expert-system concepts. This application is not validated medical software and must not replace professional clinical judgment.

## 1. How the rule engine works

When a user submits the assessment form, the application converts the form values into an initial set of facts called **working memory**.

The inference engine then performs the following cycle:

1. Compare the current facts with all rules that have not fired.
2. Add every matching rule to the **conflict set**.
3. Sort the conflict set using the metarules.
4. Fire the highest-ranked rule.
5. Add the rule's conclusions to working memory.
6. Repeat the process because the new facts may activate other rules.
7. Stop when no unfired rule is applicable.

Each rule can fire only once during one assessment. Most rules also check that their output fact does not already exist.

```text
Form inputs
    |
    v
Initial working memory
    |
    v
Match applicable rules
    |
    v
Build and rank conflict set
    |
    v
Fire one rule and add new facts
    |
    +---------- repeat ----------+
    |
    v
Final conclusion and recommendations
```

## 2. Conflict-resolution metarules

Several rules can be applicable at the same time. The engine selects one using the following order:

1. **Highest priority first**
2. **Most specific rule first**
3. **Highest confidence first**
4. **Lowest numerical rule ID first**

For example, if R15 and R9 are both applicable to a stroke patient with a tPA allergy, R15 fires first because its priority is 101 while R9 has priority 79. This ensures the allergy safety restriction is recorded before the CT recommendation.

### Specificity calculation

Specificity represents the number of conditions described by a rule. In the current implementation it is calculated from the number of `AND` conditions in the rule description.

### Rule metadata

Every rule contains:

- **ID:** Unique identifier such as R1.
- **Name:** Human-readable rule name.
- **Category:** Relation, Heuristic, Recommendation, Directive, or Strategy.
- **Priority:** Used first during conflict resolution.
- **Confidence:** Expert-system confidence metadata.
- **Conditions:** The IF part of the rule.
- **Conclusion:** The human-readable THEN result.
- **Predicate:** Executable condition that checks working memory.
- **Action:** Facts added to working memory when the rule fires.

## 3. Inputs accepted from the GUI

| GUI field | Working-memory key | Type | Example | Used by |
|---|---|---:|---|---|
| Age | `age` | Integer | `10` | R14 |
| Gender | `gender` | Text | `male` | Stored but not currently used by a rule |
| Consciousness | `consciousness` | Text | `unresponsive` | R3 |
| Heart rate | `heart_rate` | Integer, bpm | `160` | R1 |
| Systolic blood pressure | `blood_pressure` | Integer, mmHg | `75` | R1, R5 |
| Oxygen saturation | `oxygen_saturation` | Integer, percent | `80` | R2 |
| Temperature | `temperature` | Decimal, °C | `41.0` | R3, R19, R21 |
| Chest pain | `chest_pain` | Boolean | Checked | R4, R17 count |
| Sweating | `sweating` | Boolean | Checked | R4, R17 count |
| Left-arm pain | `left_arm_pain` | Boolean | Checked | R4, R17 count |
| Facial drooping | `facial_drooping` | Boolean | Checked | R6, R17 count |
| Slurred speech | `speech_slurred` | Boolean | Checked | R6, R17 count |
| Arm weakness | `arm_weakness` | Boolean | Checked | R6, R17 count |
| Trauma | `trauma` | Boolean | Checked | R7, R17 count |
| Trauma mechanism | `mechanism` | Text | `high_impact` | R7 |
| Bleeding level | `bleeding` | Text | `severe` | R5, R17 count |
| Known drug allergy | `has_allergy` | Boolean | Checked | R15 |
| Allergic drug | `allergy_drug` | Text | `tPA` | R15 |
| ICU bed available | `icu_available` | Boolean | Checked/unchecked | R12, R16 |

The patient's name is stored in the database but is not a clinical rule input.

## 4. Derived input: symptom count

The application calculates `symptom_count` before inference begins. One point is added for each of the following:

- Chest pain
- Sweating
- Left-arm pain
- Facial drooping
- Slurred speech
- Arm weakness
- Trauma
- Any bleeding level other than `none`

R17 fires when the calculated count is at least 2.

## 5. Rule categories

### Relation rules

Relation rules identify a clinical relationship between observations and a suspected state. Rules: R1, R2, R4, R5, R6, R19, and R21.

### Heuristic rules

Heuristic rules represent practical expert judgments based on recognizable patterns. Rules: R3 and R7.

### Recommendation rules

Recommendation rules propose an investigation or treatment after another condition has been inferred. Rules: R8, R9, R10, R12, R20, and R22.

### Directive rules

Directive rules specify urgent actions, restrictions, or escalation steps. Rules: R11, R13, R14, R15, and R18.

### Strategy rules

Strategy rules determine workflow, resource allocation, or multi-condition response. Rules: R16, R17, R23, and R24.

---

## 6. Complete rule descriptions

## R1 — Circulatory collapse

| Property | Value |
|---|---|
| Category | Relation |
| Priority | 100 |
| Confidence | 98% |
| Direct inputs | `heart_rate`, `blood_pressure` |

**IF**

```text
heart_rate > 150
AND blood_pressure < 80
AND patient_status has not already been inferred
```

**THEN add**

```text
patient_status = "critical"
circulatory_collapse = true
```

**How to fire it:** Enter a heart rate above 150 and systolic blood pressure below 80. For example, heart rate `160` and blood pressure `70`.

**Boundary behavior:** Heart rate exactly `150` does not match. Blood pressure exactly `80` does not match.

**Downstream effects:** The new `patient_status = critical` fact can activate R12, R13, R14, R16, and R18.

---

## R2 — Respiratory failure

| Property | Value |
|---|---|
| Category | Relation |
| Priority | 98 |
| Confidence | 97% |
| Direct input | `oxygen_saturation` |

**IF**

```text
oxygen_saturation < 85
AND respiratory_failure has not already been inferred
```

**THEN add**

```text
respiratory_failure = true
```

**How to fire it:** Enter oxygen saturation below 85%, such as `80`.

**Boundary behavior:** Oxygen saturation exactly `85` does not match.

**Downstream effects:** Activates R11 and can activate R23. It contributes one life threat toward R24.

---

## R3 — Septic shock risk

| Property | Value |
|---|---|
| Category | Heuristic |
| Priority | 97 |
| Confidence | 94% |
| Direct inputs | `temperature`, `consciousness` |

**IF**

```text
temperature > 40
AND consciousness = "unresponsive"
AND septic_shock_risk has not already been inferred
```

**THEN add**

```text
septic_shock_risk = "high"
```

**How to fire it:** Enter a temperature above 40°C and select **Unresponsive**. Example: `41°C`.

**Boundary behavior:** Temperature exactly `40°C` does not activate R3.

**Downstream effects:** Activates R20 and R23. The same temperature also activates R19 because it is at least 39°C.

---

## R4 — Cardiac event pattern

| Property | Value |
|---|---|
| Category | Relation |
| Priority | 93 |
| Confidence | 95% |
| Direct inputs | `chest_pain`, `sweating`, `left_arm_pain` |

**IF**

```text
chest_pain = true
AND sweating = true
AND left_arm_pain = true
AND cardiac_event_suspected has not already been inferred
```

**THEN add**

```text
cardiac_event_suspected = true
```

**How to fire it:** Select all three checkboxes: **Chest pain**, **Sweating**, and **Left-arm pain**.

**Downstream effects:** Activates R8 and contributes one life threat toward R24. The three selected symptoms also make R17 applicable.

---

## R5 — Hemorrhagic shock

| Property | Value |
|---|---|
| Category | Relation |
| Priority | 99 |
| Confidence | 97% |
| Direct inputs | `bleeding`, `blood_pressure` |

**IF**

```text
bleeding = "severe"
AND blood_pressure < 90
AND hemorrhagic_shock has not already been inferred
```

**THEN add**

```text
hemorrhagic_shock = true
```

**How to fire it:** Select **Severe** bleeding and enter blood pressure below 90, such as `75`.

**Boundary behavior:** Blood pressure exactly `90` does not match.

**Downstream effects:** Activates R10 and R23. It contributes one life threat toward R24.

---

## R6 — FAST stroke pattern

| Property | Value |
|---|---|
| Category | Relation |
| Priority | 96 |
| Confidence | 96% |
| Direct inputs | `facial_drooping`, `speech_slurred`, `arm_weakness` |

**IF**

```text
facial_drooping = true
AND speech_slurred = true
AND arm_weakness = true
AND stroke_suspected has not already been inferred
```

**THEN add**

```text
stroke_suspected = true
```

**How to fire it:** Select **Facial drooping**, **Slurred speech**, and **Arm weakness**.

**Downstream effects:** Activates R9. If a tPA allergy was entered, it activates R15. It also contributes one life threat toward R24.

---

## R7 — High-impact trauma

| Property | Value |
|---|---|
| Category | Heuristic |
| Priority | 88 |
| Confidence | 88% |
| Direct inputs | `trauma`, `mechanism` |

**IF**

```text
trauma = true
AND mechanism = "high_impact"
AND internal_injury_risk has not already been inferred
```

**THEN add**

```text
internal_injury_risk = "high"
```

**How to fire it:** Select **Trauma** and choose **High impact** as the trauma mechanism.

**Important:** Choosing high impact without selecting the Trauma checkbox does not fire the rule.

---

## R8 — Cardiac investigation

| Property | Value |
|---|---|
| Category | Recommendation |
| Priority | 78 |
| Confidence | 95% |
| Inferred input | `cardiac_event_suspected` from R4 |

**IF**

```text
cardiac_event_suspected = true
AND recommend_ECG has not already been inferred
```

**THEN add**

```text
recommend_ECG = true
```

**How to fire it:** Trigger R4 by selecting chest pain, sweating, and left-arm pain. Forward chaining then makes R8 applicable.

**Displayed result:** “Perform an immediate ECG.”

---

## R9 — Stroke imaging

| Property | Value |
|---|---|
| Category | Recommendation |
| Priority | 79 |
| Confidence | 96% |
| Inferred input | `stroke_suspected` from R6 |

**IF**

```text
stroke_suspected = true
AND recommend_CT has not already been inferred
```

**THEN add**

```text
recommend_CT = true
```

**How to fire it:** Trigger R6 by selecting all three stroke indicators. R9 then fires during a later forward-chaining cycle.

**Displayed result:** “Perform an urgent CT scan.”

---

## R10 — Replace blood loss

| Property | Value |
|---|---|
| Category | Recommendation |
| Priority | 84 |
| Confidence | 94% |
| Inferred input | `hemorrhagic_shock` from R5 |

**IF**

```text
hemorrhagic_shock = true
AND recommend_blood_transfusion has not already been inferred
```

**THEN add**

```text
recommend_blood_transfusion = true
```

**How to fire it:** Trigger R5 with severe bleeding and blood pressure below 90.

**Displayed result:** “Prepare a blood transfusion.”

---

## R11 — Airway protection

| Property | Value |
|---|---|
| Category | Directive |
| Priority | 86 |
| Confidence | 96% |
| Inferred input | `respiratory_failure` from R2 |

**IF**

```text
respiratory_failure = true
AND recommend_intubation has not already been inferred
```

**THEN add**

```text
recommend_intubation = true
```

**How to fire it:** Enter oxygen saturation below 85 to trigger R2. R11 then fires in a later cycle.

**Displayed result:** “Prepare immediate intubation.”

---

## R12 — ICU admission

| Property | Value |
|---|---|
| Category | Recommendation |
| Priority | 76 |
| Confidence | 92% |
| Inputs | Inferred `patient_status`; direct `icu_available` |

**IF**

```text
patient_status = "critical"
AND icu_available = true
AND recommend_ICU has not already been inferred
```

**THEN add**

```text
recommend_ICU = true
```

**How to fire it:** Make the patient critical through R1 or R23 and leave **ICU bed available** selected.

**Displayed result:** “Admit patient to ICU.”

**Conflict relationship:** R12 and R16 are mutually exclusive because ICU availability cannot be true and false simultaneously.

---

## R13 — Red alert escalation

| Property | Value |
|---|---|
| Category | Directive |
| Priority | 90 |
| Confidence | 99% |
| Inferred input | `patient_status = critical` from R1 or R23 |

**IF**

```text
patient_status = "critical"
AND alert_level has not already been inferred
```

**THEN add**

```text
alert_level = "RED"
notify_senior_doctor = true
```

**How to fire it:** Make the patient critical through R1 or R23.

**Default alternative:** If no rule sets an alert level, the engine adds `alert_level = GREEN` after inference stops.

---

## R14 — Pediatric escalation

| Property | Value |
|---|---|
| Category | Directive |
| Priority | 85 |
| Confidence | 95% |
| Inputs | Direct `age`; inferred `patient_status` |

**IF**

```text
age < 12
AND patient_status = "critical"
AND notify_pediatric has not already been inferred
```

**THEN add**

```text
notify_pediatric = true
```

**How to fire it:** Enter an age below 12 and make the patient critical through R1 or R23. Example: age `10`, heart rate `160`, and blood pressure `70`.

**Boundary behavior:** Age exactly `12` does not match.

---

## R15 — tPA allergy safety

| Property | Value |
|---|---|
| Category | Directive |
| Priority | 101 — highest in the knowledge base |
| Confidence | 99% |
| Inputs | Inferred `stroke_suspected`; direct allergy fields |

**IF**

```text
stroke_suspected = true
AND has_allergy = true
AND allergy_drug, after trimming and lowercasing, equals "tpa"
AND tPA_blocked has not already been inferred
```

**THEN add**

```text
tPA_blocked = true
administer_tPA = false
```

**How to fire it:** Select all three stroke indicators, select **Known drug allergy**, and enter `tPA` as the allergic drug.

**Text matching:** `tPA`, `TPA`, `tpa`, and values with surrounding spaces all match. Other drug names do not.

**Conflict behavior:** After R6 produces `stroke_suspected`, both R15 and R9 may be applicable. R15 fires first because it has the highest priority.

---

## R16 — Unavailable ICU strategy

| Property | Value |
|---|---|
| Category | Strategy |
| Priority | 89 |
| Confidence | 98% |
| Inputs | Inferred `patient_status`; direct `icu_available` |

**IF**

```text
patient_status = "critical"
AND icu_available = false
AND emergency_transfer has not already been inferred
```

**THEN add**

```text
emergency_transfer = true
```

**How to fire it:** Make the patient critical through R1 or R23 and clear the **ICU bed available** checkbox.

**Displayed result:** “Arrange emergency transfer.”

---

## R17 — Multiple-symptom strategy

| Property | Value |
|---|---|
| Category | Strategy |
| Priority | 65 — lowest in the knowledge base |
| Confidence | 85% |
| Derived input | `symptom_count` |

**IF**

```text
symptom_count >= 2
AND vitals_first has not already been inferred
```

**THEN add**

```text
vitals_first = true
```

**How to fire it:** Select any two counted symptoms. For example, select chest pain and sweating. A non-`none` bleeding selection counts as one symptom.

**Why it often fires last:** Its priority is 65, so urgent diagnostic and safety rules are selected before it when they are applicable.

---

## R18 — Critical triage bypass

| Property | Value |
|---|---|
| Category | Directive |
| Priority | 87 |
| Confidence | 98% |
| Inferred input | `patient_status = critical` from R1 or R23 |

**IF**

```text
patient_status = "critical"
AND skip_triage has not already been inferred
```

**THEN add**

```text
skip_triage = true
```

**How to fire it:** Make the patient critical through R1 or R23.

**Displayed result:** “Bypass routine triage queue.”

---

## R19 — High fever

| Property | Value |
|---|---|
| Category | Relation |
| Priority | 72 |
| Confidence | 90% |
| Direct input | `temperature` |

**IF**

```text
temperature >= 39
AND infection_risk has not already been inferred
```

**THEN add**

```text
infection_risk = "high"
```

**How to fire it:** Enter a temperature of at least 39°C.

**Boundary behavior:** Temperature exactly `39°C` matches.

**Important:** R19 alone does not set the patient to critical and does not start the sepsis protocol. R3 is required for the septic-shock chain.

---

## R20 — Sepsis treatment

| Property | Value |
|---|---|
| Category | Recommendation |
| Priority | 82 |
| Confidence | 91% |
| Inferred input | `septic_shock_risk = high` from R3 |

**IF**

```text
septic_shock_risk = "high"
AND recommend_sepsis_protocol has not already been inferred
```

**THEN add**

```text
recommend_sepsis_protocol = true
```

**How to fire it:** Enter temperature above 40°C and select Unresponsive to trigger R3.

**Displayed result:** “Start sepsis protocol and urgent antibiotics.”

---

## R21 — Hypothermia

| Property | Value |
|---|---|
| Category | Relation |
| Priority | 73 |
| Confidence | 94% |
| Direct input | `temperature` |

**IF**

```text
temperature < 35
AND hypothermia has not already been inferred
```

**THEN add**

```text
hypothermia = true
```

**How to fire it:** Enter a temperature below 35°C, such as `34`.

**Boundary behavior:** Temperature exactly `35°C` does not match.

**Downstream effects:** Activates R22.

---

## R22 — Active warming

| Property | Value |
|---|---|
| Category | Recommendation |
| Priority | 74 |
| Confidence | 93% |
| Inferred input | `hypothermia` from R21 |

**IF**

```text
hypothermia = true
AND recommend_warming has not already been inferred
```

**THEN add**

```text
recommend_warming = true
```

**How to fire it:** Enter temperature below 35°C to trigger R21. R22 then fires in the next forward-chaining cycle.

**Displayed result:** “Begin active warming.”

---

## R23 — Life-threat escalation

| Property | Value |
|---|---|
| Category | Strategy |
| Priority | 92 |
| Confidence | 96% |
| Inferred inputs | R2, R3, or R5 output |

**IF**

At least one of the following is true:

```text
respiratory_failure = true
OR hemorrhagic_shock = true
OR septic_shock_risk = "high"
```

and:

```text
patient_status has not already been inferred
```

**THEN add**

```text
patient_status = "critical"
```

**How to fire it:** Trigger any one of R2, R3, or R5:

- Oxygen saturation below 85; or
- Temperature above 40°C with Unresponsive selected; or
- Severe bleeding with blood pressure below 90.

**Downstream effects:** Activates R12 or R16, plus R13 and R18. If the patient was already made critical by R1, R23 does not fire because `patient_status` already exists.

---

## R24 — Multi-threat response

| Property | Value |
|---|---|
| Category | Strategy |
| Priority | 95 |
| Confidence | 97% |
| Inferred inputs | Outputs of R2, R4, R5, and R6 |

R24 counts these four possible life-threat facts:

```text
respiratory_failure
hemorrhagic_shock
cardiac_event_suspected
stroke_suspected
```

**IF**

```text
at least two of the four life-threat facts are true
AND activate_emergency_team has not already been inferred
```

**THEN add**

```text
activate_emergency_team = true
```

**How to fire it:** Trigger any two of R2, R4, R5, and R6. Example:

- Oxygen saturation `80` to trigger R2; and
- Severe bleeding with blood pressure `75` to trigger R5.

**Important:** `septic_shock_risk` and `internal_injury_risk` are not included in the R24 count in the current implementation.

**Displayed result:** “Activate emergency response team.”

---

## 7. Rule dependency map

```text
R1  -> critical -> R12 or R16
                -> R13
                -> R14 when age < 12
                -> R18

R2  -> respiratory failure -> R11
                          \-> R23 -> critical chain
                           \-> contributes to R24

R3  -> septic-shock risk -> R20
                        \-> R23 -> critical chain
R3 input also makes R19 applicable

R4  -> cardiac event -> R8
                   \-> contributes to R24

R5  -> hemorrhagic shock -> R10
                        \-> R23 -> critical chain
                         \-> contributes to R24

R6  -> stroke suspected -> R9
                       \-> R15 when tPA allergy exists
                        \-> contributes to R24

R7  -> internal-injury risk

R17 <- any two counted symptoms

R19 -> infection risk

R21 -> hypothermia -> R22
```

## 8. Demonstration cases

### Case A: Cardiac collapse conflict

Enter:

```text
Heart rate: 160
Blood pressure: 70
Chest pain: selected
Sweating: selected
Left-arm pain: selected
ICU available: selected
```

Expected fired-rule order:

```text
R1, R4, R13, R18, R8, R12, R17
```

Why multiple rules apply:

- R1 matches the vital signs.
- R4 matches the three cardiac symptoms.
- After R1, critical-status rules R13, R18, and R12 become applicable.
- After R4, R8 becomes applicable.
- Three symptoms make R17 applicable.

### Case B: Pediatric stroke with tPA allergy

Enter:

```text
Age: 10
Heart rate: 160
Blood pressure: 70
Facial drooping: selected
Slurred speech: selected
Arm weakness: selected
Known drug allergy: selected
Allergic drug: tPA
ICU available: not selected
```

Expected fired-rule order:

```text
R1, R6, R15, R13, R16, R18, R14, R9, R17
```

This case demonstrates safety priority because R15 blocks tPA before the lower-priority R9 imaging recommendation fires.

### Case C: Multi-system trauma

Enter:

```text
Oxygen saturation: 80
Blood pressure: 75
Bleeding: severe
Trauma: selected
Trauma mechanism: high impact
ICU available: selected
```

Expected fired-rule order:

```text
R5, R2, R24, R23, R13, R7, R18, R11, R10, R12, R17
```

This case demonstrates:

- Two initial emergency relations, R5 and R2
- Multi-threat activation through R24
- Critical escalation through R23
- Several downstream directives and recommendations

### Case D: Septic-shock chain

Enter:

```text
Temperature: 41
Consciousness: unresponsive
ICU available: selected
```

Expected fired-rule order:

```text
R3, R23, R13, R18, R20, R12, R19
```

### Case E: Hypothermia chain

Enter:

```text
Temperature: 34
```

Expected fired-rule order:

```text
R21, R22
```

The final default conclusion remains GREEN and stable because these rules do not set `patient_status` to critical.

## 9. Default conclusion

After no more rules can fire, the engine supplies defaults when they were not inferred:

```text
alert_level = "GREEN"
patient_status = "stable"
```

These defaults are not separate knowledge-base rules and are not included in the fired-rule list.

## 10. How to verify rules in the application

1. Start the Flask application.
2. Open `http://127.0.0.1:5000`.
3. Enter one of the test cases in this document.
4. Select **Run inference engine**.
5. Confirm the final conclusion and recommendations.
6. Check the **Rules fired** section.
7. Expand **Explanation trace**.
8. For every cycle, verify:
   - The applicable rules in the conflict set
   - The rule selected by the metarules
   - Its priority, specificity, and confidence
   - The new facts added to working memory

The automated rule-coverage test can also be run with:

```powershell
python -m unittest -v
```

`test_all_24_rules_are_reachable` verifies that the five prepared cases collectively fire every rule from R1 through R24.
