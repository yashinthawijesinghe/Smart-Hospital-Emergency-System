import os
import tempfile
import unittest

import database
from app import app, facts_from_patient, run_expert_system


def patient(**updates):
    data = {
        "name": "Rule Test", "age": 35, "gender": "male", "heart_rate": 80,
        "blood_pressure": 120, "oxygen_saturation": 98, "temperature": 37,
        "consciousness": "responsive", "chest_pain": False, "sweating": False,
        "left_arm_pain": False, "bleeding": "none", "facial_drooping": False,
        "speech_slurred": False, "arm_weakness": False, "trauma": False,
        "mechanism": "none", "has_allergy": False, "allergy_drug": "",
        "icu_available": True,
    }
    data.update(updates)
    return data


class ExpertSystemTests(unittest.TestCase):
    def test_all_24_rules_are_reachable(self):
        cases = [
            patient(heart_rate=160, blood_pressure=70, chest_pain=True,
                    sweating=True, left_arm_pain=True),
            patient(age=10, heart_rate=160, blood_pressure=70,
                    facial_drooping=True, speech_slurred=True, arm_weakness=True,
                    has_allergy=True, allergy_drug="tPA", icu_available=False),
            patient(oxygen_saturation=80, blood_pressure=75, bleeding="severe",
                    trauma=True, mechanism="high_impact"),
            patient(temperature=41, consciousness="unresponsive"),
            patient(temperature=34),
        ]
        fired = set()
        for data in cases:
            _, rules, trace = run_expert_system(facts_from_patient(data))
            fired.update(rules)
            self.assertEqual(len(rules), len(trace))
        self.assertEqual(fired, {f"R{number}" for number in range(1, 25)})

    def test_priority_metarule_selects_safety_rule(self):
        facts, rules, trace = run_expert_system(facts_from_patient(patient(
            heart_rate=160, blood_pressure=70, facial_drooping=True,
            speech_slurred=True, arm_weakness=True, has_allergy=True,
            allergy_drug="tPA",
        )))
        self.assertLess(rules.index("R15"), rules.index("R9"))
        self.assertTrue(facts["tPA_blocked"])
        self.assertIn("priority", trace[0]["reason"])

    def test_stable_patient_has_green_conclusion(self):
        facts, rules, _ = run_expert_system(facts_from_patient(patient()))
        self.assertEqual(rules, [])
        self.assertEqual(facts["patient_status"], "stable")
        self.assertEqual(facts["alert_level"], "GREEN")


class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handle, cls.database_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        database.DATABASE = cls.database_path
        database.init_db()
        app.config.update(TESTING=True)
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.database_path)

    def test_pages_and_search(self):
        for path in ("/", "/dashboard", "/dashboard?q=test", "/rules"):
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_assessment_is_saved_and_displayed(self):
        response = self.client.post("/submit", data={
            "name": "Demo Patient", "age": "35", "gender": "male",
            "heart_rate": "160", "blood_pressure": "70",
            "oxygen_saturation": "98", "temperature": "37",
            "consciousness": "responsive", "chest_pain": "on",
            "sweating": "on", "left_arm_pain": "on", "bleeding": "none",
            "mechanism": "none", "icu_available": "on",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Inference complete", response.data)
        self.assertIn(b"Demo Patient", response.data)
        self.assertIn(b"R1", response.data)
        self.assertIn(b"Perform an immediate ECG", response.data)

    def test_missing_result_returns_404(self):
        self.assertEqual(self.client.get("/result/99999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
