# EmergencyLens — Smart Hospital Emergency Expert System

EmergencyLens is a web-based Rule-Based Expert System (RBES) created as an educational emergency-triage project. A user enters patient details, vital signs, symptoms, trauma information, allergies, and ICU availability. The inference engine evaluates its knowledge base, resolves simultaneously applicable rules, and produces an explainable conclusion and recommendations.

> **Educational warning:** This application demonstrates expert-system concepts. It is not validated medical software and must not replace assessment by qualified healthcare professionals.

## Main features

- 24 meaningful and reachable IF–THEN rules
- Relation, Recommendation, Directive, Strategy, and Heuristic rule categories
- Forward-chaining inference until no new fact can be produced
- Conflict-set construction during every inference cycle
- Explicit metarules for selecting between applicable rules
- SQLite storage for patients, diagnoses, inferred facts, and reasoning traces
- Browser-based GUI for entering observations and running inference
- Dedicated result screen containing the conclusion and recommendations
- Searchable patient-record dashboard
- Fired-rule list and cycle-by-cycle explanation trace
- Rule Guide explaining how to activate every rule
- Three prepared multi-rule conflict demonstrations
- Automated engine, database, route, and rule-coverage tests

## Technology stack

- Python 3
- Flask 3
- SQLite 3 through Python's built-in `sqlite3` module
- Jinja HTML templates
- Plain CSS
- Python `unittest` test suite

No external database server or JavaScript framework is required.

## Project structure

```text
Smart-Hospital-Emergency-System/
├── app.py                    # Flask routes, knowledge base, and inference engine
├── database.py               # SQLite schema, migrations, storage, and search
├── requirements.txt          # Python packages and versions
├── test_system.py            # Automated tests and all-rule coverage cases
├── hospital.db               # Local runtime database; created automatically
├── static/
│   ├── styles.css            # Shared interface styles
│   └── result.css            # Result-screen styles
└── templates/
    ├── index.html            # New patient assessment form
    ├── result.html           # Immediate inference result
    ├── dashboard.html        # Searchable patient history
    ├── rules.html            # Knowledge base, flow, and conflict scenarios
    └── not_found.html        # Missing-result page
```

## System architecture

```text
Patient observations entered in GUI
                 |
                 v
        Initial working memory
                 |
                 v
     Match all unfired IF conditions
                 |
                 v
          Build conflict set
                 |
                 v
           Apply metarules
                 |
                 v
         Fire one selected rule
                 |
                 v
     Add conclusions as new facts
                 |
                 +------ repeat matching ------+
                 |
                 v
     Store result and reasoning trace
                 |
                 v
   Display conclusion and recommendations
```

## Knowledge base

The knowledge base contains rules R1–R24. It covers:

- Circulatory collapse
- Respiratory failure
- Septic-shock risk
- Cardiac-event patterns
- Hemorrhagic shock
- FAST stroke indicators
- High-impact trauma
- ECG and CT recommendations
- Blood transfusion and intubation
- ICU admission and emergency transfer
- Pediatric and senior-doctor escalation
- tPA allergy safety
- Multiple-symptom triage strategy
- High fever, hypothermia, and warming
- Sepsis protocol
- Multi-threat emergency-team activation

Open **Rule Guide** in the running application to see every rule's exact IF conditions, THEN conclusion, category, priority, specificity, confidence, and test inputs.

## Forward chaining

The engine begins with facts entered by the user. It repeatedly:

1. Evaluates every rule that has not already fired.
2. Collects applicable rules into a conflict set.
3. Uses metarules to select one winner.
4. Fires the winner and adds its conclusion to working memory.
5. Re-evaluates the knowledge base using the newly inferred facts.
6. Stops when no rule remains applicable.

The result page stores and displays every cycle, including the conflict set, selected rule, selection reason, and facts added.

## Conflict-resolution metarules

Applicable rules are ranked in this order:

1. **Highest priority first** — safety-critical actions take precedence.
2. **Most specific first** — a rule with more conditions wins a priority tie.
3. **Highest confidence first** — stronger expert knowledge wins the next tie.
4. **Lowest rule number first** — provides a deterministic final tie-break.

The Rule Guide provides three conflict scenarios: cardiac collapse, pediatric stroke with a tPA allergy, and multi-system trauma.

## Database

SQLite data is stored locally in `hospital.db`. The application creates or migrates the database automatically at startup.

The database contains:

- `patients`: submitted identity, vital-sign, symptom, trauma, allergy, and resource facts
- `diagnoses`: final status, alert level, fired rules, all inferred facts, and the reasoning trace

`hospital.db` is ignored by Git because it is runtime data. Every new clone creates its own clean database when the application starts.

## Clone and run on Windows

### Prerequisites

Install:

- [Git](https://git-scm.com/downloads)
- Python 3.10 or newer

During Python installation on Windows, select **Add Python to PATH**.

### Commands using PowerShell

```powershell
git clone <YOUR-REPOSITORY-URL>
cd Smart-Hospital-Emergency-System
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

Replace `<YOUR-REPOSITORY-URL>` with the GitHub repository URL.

If PowerShell blocks virtual-environment activation, allow it for only the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open <http://127.0.0.1:5000> in a browser.

Stop the server with `Ctrl+C`. Leave the virtual environment with:

```powershell
deactivate
```

## Clone and run on macOS or Linux

```bash
git clone <YOUR-REPOSITORY-URL>
cd Smart-Hospital-Emergency-System
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>.

## Using the application

1. Open **New assessment**.
2. Enter patient information and current vital signs.
3. Select all observed symptoms and relevant trauma information.
4. Enter allergy and ICU availability information.
5. Select **Run inference engine**.
6. Review the dedicated result page.
7. Expand **Explanation trace** to inspect forward chaining and conflict resolution.
8. Use **Patient records** to search earlier assessments.
9. Use **Rule guide** to learn how to trigger and demonstrate every rule.

## Run automated tests

Activate the virtual environment and run:

```powershell
python -m unittest -v
```

The test suite verifies:

- All 24 rules are reachable
- Safety-priority conflict resolution
- Stable GREEN conclusions
- Application routes
- Database persistence
- Dedicated inference results
- Missing-result handling
- Patient searching

## Reset the local database

Stop the Flask server first. To erase all patient and diagnosis records while preserving the schema, run from the project directory:

```powershell
python -c "import sqlite3; c=sqlite3.connect('hospital.db'); c.execute('DELETE FROM diagnoses'); c.execute('DELETE FROM patients'); c.execute('DELETE FROM sqlite_sequence WHERE name=? OR name=?', ('patients', 'diagnoses')); c.commit(); c.execute('VACUUM'); c.close(); print('Database reset complete')"
```

Alternatively, because the application recreates the database, delete the local database after stopping the server:

```powershell
Remove-Item -LiteralPath .\hospital.db
python app.py
```

## Git cleanup for files committed before `.gitignore`

`.gitignore` does not automatically untrack files already committed. Existing clones should run this one time:

```powershell
git rm -r --cached -- __pycache__
git rm --cached -- hospital.db
git add .gitignore README.md
git commit -m "Remove generated files and update project documentation"
git push
```

These commands remove generated files only from Git tracking. They do not delete the local `hospital.db` file or local cache directory.

The old dashboard-generation helpers are no longer used by the application. If the team does not need them, remove them from both Git and the working directory with:

```powershell
git rm -- make_dash.py templates/fix_dashboard.py
git commit -m "Remove obsolete dashboard helper scripts"
git push
```

To remove every currently tracked file that is now ignored in one command and then re-stage the repository safely:

```powershell
git rm -r --cached .
git add .
git status
git commit -m "Apply gitignore to tracked files"
git push
```

Always inspect `git status` before committing the broader cleanup command.

## Development notes

- Keep clinical thresholds and recommendations in the knowledge base auditable.
- Add new rules as `Rule` objects with an ID, category, priority, confidence, condition description, predicate, and action.
- Rules should add a new fact and should remain reachable through GUI inputs or earlier inferences.
- Extend `test_system.py` whenever the knowledge base changes.
- Never commit `.env`, virtual environments, Python caches, or real patient data.

## License and use

This repository is intended for coursework, demonstrations, and learning about knowledge representation and inference. It is not approved for clinical deployment.
