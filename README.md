# MedTourEasy — Patient Conversion & Provider Performance Intelligence

Analytics project identifying where international healthcare leads lose
momentum, which providers convert most efficiently, and which patients
require proactive intervention.

## Project Structure

```
mte-analytics/
├── data/
│   ├── raw/                    # original CSVs + mte_patient_intelligence.db
│   └── processed/              # cleaned dataframes exported
├── notebooks/
│   ├── 01_data_quality_report.ipynb
│   ├── 02_exploratory_patient_funnel_analysis.ipynb
│   ├── 03_sql_provider_scorecard.ipynb
│   ├── 04_modeling_dropoff_and_completion.ipynb
│   └── 05_segmentation_and_recommendations.ipynb
├── sql/
│   ├── 03_sql_provider_scorecard.sql
│
├── src/
│   ├── data_cleaning.py
│   ├── funnel_analysis.py
│   └── modeling_utils.py
├── reports/
│   └── final_memo.md
├── README.md
└── requirements.txt
```

## How to Reproduce

1. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/scripts/activate
   pip install -r requirements.txt
   ```
2. Place the provided data files in `data/raw/`:
   - `patient_journey.csv`
   - `provider_master.csv`
   - `communication_logs.csv`
   - `treatment_outcomes.csv`
   - `country_reference.csv`
   - `mte_patient_intelligence.db`
3. Run notebooks in order (01 -> 02 -> 03 -> 04 -> 05). Notebook 01 exports a
   cleaned dataset to `data/processed/`, which later notebooks read from.
4. Run `sql/03_sql_provider_scorecard.sql` against `mte_patient_intelligence.db`

## Notebook Summaries

| Notebook | Purpose | Key Output |
|---|---|---|
| 01 | Data quality profiling: nulls, duplicates, dtype checks, CSV/DB consistency | Cleaned dataset, assumptions log |
| 02 | Funnel reconciliation, KPI calculation, drop-off analysis, SLA breach impact | Reconciled funnel table, key findings |
| 03 (SQL) | Provider scorecard, cohort conversion, hypothesis-test prep | `provider_scorecard.csv` |
| 04 | Predictive modeling: treatment completion & drop-off risk | Model comparison, feature importance |
| 05 | Patient and provider segmentation (KMeans) | Segment profiles + recommendations |

## Key Findings (Summary)

- **SLA breach is the highest-leverage lever**: 82.8% of patients experience
  a response-time SLA breach; breaches correlate with a ~17pp drop in both
  consultation booking and treatment completion.
- **Provider performance varies ~2x** across the 30 providers, but rankings
  are partially confounded by case mix (urgency).
- **Urgent cases complete treatment at a lower rate** than Routine cases —
  a counterintuitive finding worth operational investigation.
- **Two patient segments** identified: a low-engagement/high-risk group and
  a high-engagement/high-value group, with a 3x difference in completion rate.
- **Two provider tiers** identified, with a ~15pp gap in treatment completion.

Full findings, quantified recommendations, and model limitations are in
`reports/final_memo.md`.

## Data Ethics & Limitations

- No clinical or diagnostic claims are made anywhere in this analysis.
- No personal identifiers beyond `patient_id` were used.
- Predictive models exclude any post-inquiry funnel signals (e.g.
  consultation_booked, quote_shared, follow_up_completed) to avoid data
  leakage; this caps achievable model performance and is documented as
  an intentional, honest limitation rather than a modeling failure.
- All ambiguous data-cleaning decisions are logged in each notebook's
  assumptions log section.

## Author

AYAN SUVRA BOSU — Data Science Intern, Healthcare Analytics / Data Science