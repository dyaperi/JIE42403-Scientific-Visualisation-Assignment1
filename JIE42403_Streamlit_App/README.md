# JIE42403 — Malaysia Demographic Explorer 

A reproducible, 3-page scientific visualisation dashboard built with Python, Pandas, Plotly and Streamlit.

## Project structure

```text
JIE42403_Streamlit_App/
├── app.py                         # Streamlit entrypoint, global filters + navigation
├── shared.py                      # CSV validation and chart functions
├── pages/
│   ├── 1_Demographic_Trends.py    # Objective 1: 3 charts
│   ├── 2_Relationship_Analysis.py # Objective 2: 3 charts
│   └── 3_State_Comparison.py      # Objective 3: 3 charts
├── data/
│   └── processed/
│       └── demography_merged_2017_2024.csv
├── requirements.txt
└── README.md
```

## Run locally (VS Code, Windows PowerShell)

1. Extract this ZIP, then open **this exact folder** in VS Code (File > Open Folder).
2. Use Terminal > New Terminal. Run `dir` and check `app.py` and `requirements.txt` are listed.
3. Install the packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Launch the app:

   ```powershell
   python -m streamlit run app.py
   ```

5. Open the local browser URL shown in the terminal (typically `http://localhost:8501`).
6. Use the Streamlit sidebar to change state selection and years. Navigate among **3 pages**.
7. To stop the local server, press Ctrl+C in the terminal.

**Important:** You do not need to run `preprocess.py` again. The processed dataset is already included. For a fresh data merge, return to your Step 3 project and copy its generated CSV into `data/processed/` here.

## Deploy to GitHub and Streamlit Community Cloud

1. Create a **new GitHub repository**, for example `jie42403-demographic-explorer`.
2. Upload the **contents** of `JIE42403_Streamlit_App` into the repository root. The repository root should show `app.py`, `shared.py`, `requirements.txt`, `pages/`, and `data/`.
3. Verify `data/processed/demography_merged_2017_2024.csv` is present in GitHub and commit the files.
4. Go to [Streamlit Community Cloud](https://share.streamlit.io/) and choose **Create app** (or **New app**), then **Deploy a public app from GitHub**.
5. Select the repository and branch, and set **Main file path** to `app.py`.
6. Deploy. Open the generated URL and check all three pages and their filters.

Deployment settings and UI labels can change; use Streamlit's deployment guide if your screen differs.

## Charts mapped to assignment objectives

| Page | Objective | Charts |
|---|---|---|
| 1: Demographic Trends | Describe marriage, birth and population changes | 1. Female marriage line chart; 2. Live-birth line chart; 3. Summed selected-state population area chart |
| 2: Relationship Analysis | Study relationships among published rates and population | 4. Scatter plot + pooled trend; 5. Pearson correlation heatmap; 6. Indexed rate trend comparison for a selected state |
| 3: State Comparison | Compare rates and population between states | 7. Crude birth rate ranking; 8. State-by-year marriage rate heatmap; 9. Population × birth-rate bubble plot sized by marriage rate |

Each page contains an objective statement, summary metrics, three visualisations and dynamic interpretation notes. A common sidebar provides interactive state selection and year filtering.

## Data information / statistical cautions

- Contains 128 rows (16 states/federal territories × 8 years, 2017–2024).
- Female marriage count/rate refers to women by state of residence; do not sum male and female marriage data.
- Female marriage rate and crude birth rate have **different population denominators**.
- Aggregated counts are safe to sum over selected states; **do not add rates**. This app only compares the originally published state-level rates, with individual-state indexing where needed.
- Page 2 Pearson correlations pool state-year records; observations are repeated by state and time, so the results are **descriptive**, not causal or inferential.
- The assignment brief says **one dataset**. Ask your lecturer whether a single master dataset produced by joining three OpenDOSM source datasets is acceptable.

## Original open data / attribution

- [Annual Marriages by State](https://open.dosm.gov.my/data-catalogue/marriages_state)
- [Annual Live Births by State](https://open.dosm.gov.my/data-catalogue/births_annual_state)
- [Population Table: States](https://open.dosm.gov.my/data-catalogue/population_state)

Published by the Department of Statistics Malaysia (DOSM), with relevant data from the National Registration Department (JPN). Data accessed as part of the assignment. Follow attribution requirements of the source datasets.

## Submission reminder

The assignment calls for **Streamlit URL + PDF report (maximum 5 pages)**, including the dataset justification and interpretation of all nine charts. The Streamlit project here is Step 5; the PDF report is not included.
