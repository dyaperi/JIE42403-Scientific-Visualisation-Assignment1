"""JIE42403 - Three linked OpenDOSM scientific visualizations (live Parquet)."""
from datetime import date
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

START_YEAR, END_YEAR = 2017, 2024
SOURCES = {
    "marriages": "https://storage.dosm.gov.my/demography/marriages_state.parquet",
    "births": "https://storage.dosm.gov.my/demography/birth_state.parquet",
    "population": "https://storage.dosm.gov.my/population/population_state.parquet",
}
PLOT_COLORS = {"Female marriages": "#2563eb", "Live births": "#0d9488", "Population": "#ea580c"}

# BEGIN PIPELINE

def prepare_data(marriages_raw: pd.DataFrame, births_raw: pd.DataFrame,
                 population_raw: pd.DataFrame) -> pd.DataFrame:
    """Return unique, validated state-year rows from three official source datasets."""
    def years(frame):
        data = frame.copy()
        data["year"] = pd.to_datetime(data["date"]).dt.year
        data["state"] = data["state"].astype(str).str.strip()
        return data.loc[data["year"].between(START_YEAR, END_YEAR)]

    marriages = years(marriages_raw)
    marriages = (marriages.loc[marriages["sex"].eq("female"),
                              ["state", "year", "abs", "rate"]]
                 .rename(columns={"abs": "female_marriages",
                                  "rate": "female_marriage_rate"}))

    births = (years(births_raw)[["state", "year", "abs", "rate"]]
              .rename(columns={"abs": "live_births", "rate": "crude_birth_rate"}))

    population = years(population_raw)
    population = (population.loc[
        population["sex"].eq("both")
        & population["age"].eq("overall")
        & population["ethnicity"].eq("overall"),
        ["state", "year", "population"]
    ].rename(columns={"population": "total_population"}))
    # OpenDOSM population is in thousands of people; convert to people.
    population["total_population"] = population["total_population"] * 1000

    for title, frame in [("marriages", marriages), ("births", births),
                         ("population", population)]:
        if frame.duplicated(["state", "year"]).any():
            raise ValueError(f"Duplicate state-year keys in {title} source")

    merged = (marriages.merge(births, on=["state", "year"], validate="one_to_one")
              .merge(population, on=["state", "year"], validate="one_to_one")
              .sort_values(["state", "year"]).reset_index(drop=True))
    numeric_cols = ["female_marriages", "female_marriage_rate",
                    "live_births", "crude_birth_rate", "total_population"]
    if merged[numeric_cols].isna().any().any():
        raise ValueError("Missing values found after merging; inspect official source updates")
    if merged["state"].nunique() != 16 or len(merged) != 16 * (END_YEAR - START_YEAR + 1):
        raise ValueError(f"Expected 128 state-year records; found {len(merged)}")
    return merged

# END PIPELINE

# BEGIN VISUALS

def chart1_indexed_trends(data: pd.DataFrame, states: list[str]) -> go.Figure:
    """Three-source indexed national or selected-states time trends; 2017=100."""
    subset = data.loc[data["state"].isin(states)]
    yearly = (subset.groupby("year", as_index=False)[
        ["female_marriages", "live_births", "total_population"]].sum())
    lookup = {
        "female_marriages": "Female marriages",
        "live_births": "Live births",
        "total_population": "Population",
    }
    for col, label in lookup.items():
        base = yearly.loc[yearly["year"].eq(START_YEAR), col].iloc[0]
        if base <= 0:
            raise ValueError(f"Cannot index {label} with a zero 2017 baseline")
        yearly[label] = yearly[col] / base * 100
    long = yearly.melt(id_vars="year", value_vars=list(lookup.values()),
                       var_name="Indicator", value_name="Index")
    fig = px.line(long, x="year", y="Index", color="Indicator", markers=True,
                  color_discrete_map=PLOT_COLORS,
                  title="1. Indexed marriage, birth and population trends (2017 = 100)",
                  labels={"year": "Year", "Index": "Index (2017 = 100)"})
    fig.add_hline(y=100, line_dash="dash", line_color="#94a3b8", opacity=0.7)
    fig.update_xaxes(dtick=1, tickformat="d")
    fig.update_layout(hovermode="x unified", legend_title_text="", height=420)
    return fig


def chart2_population_bubbles(data: pd.DataFrame, year: int,
                              states: list[str]) -> tuple[go.Figure, float]:
    """X=marriage rate, Y=birth rate, bubble area=total population."""
    subset = data.loc[data["year"].eq(year) & data["state"].isin(states)].copy()
    subset["Population (millions)"] = subset["total_population"] / 1_000_000
    fig = px.scatter(
        subset, x="female_marriage_rate", y="crude_birth_rate",
        size="total_population", size_max=55, hover_name="state",
        color="state", color_discrete_sequence=px.colors.qualitative.Alphabet,
        hover_data={"Population (millions)": ":.2f", "total_population": False,
                    "female_marriages": ":,.0f", "live_births": ":,.0f", "year": False},
        title=f"2. Marriage–birth rate association; population size ({year})",
        labels={"female_marriage_rate": "Female marriages per 1,000 unmarried women",
                "crude_birth_rate": "Live births per 1,000 people",
                "state": "State"},
    )
    fig.update_traces(marker=dict(opacity=0.75, line=dict(width=1, color="white")))
    fig.update_layout(showlegend=False, height=470)
    corr = subset["female_marriage_rate"].corr(subset["crude_birth_rate"])
    if len(subset) >= 3 and subset["female_marriage_rate"].nunique() > 1:
        slope, intercept = np.polyfit(subset["female_marriage_rate"],
                                      subset["crude_birth_rate"], deg=1)
        xs = np.linspace(subset["female_marriage_rate"].min(),
                         subset["female_marriage_rate"].max(), 100)
        fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines",
                                 name="Descriptive linear fit", showlegend=False,
                                 line=dict(color="#334155", dash="dash", width=2)))
    return fig, float(corr) if pd.notna(corr) else float("nan")


def chart3_state_heatmap(data: pd.DataFrame, year: int,
                         states: list[str]) -> go.Figure:
    """Z-scores within each 2024 indicator, across currently selected states."""
    subset = (data.loc[data["year"].eq(year) & data["state"].isin(states)]
              .sort_values("state"))
    metrics = {
        "female_marriage_rate": "Marriage rate",
        "crude_birth_rate": "Birth rate",
        "total_population": "Population",
    }
    raw = subset.set_index("state")[list(metrics)].rename(columns=metrics)
    # Standardize across states for each metric, not across mixed units.
    mu = raw.mean(axis=0)
    sd = raw.std(axis=0, ddof=0).replace(0, np.nan)
    zscores = (raw - mu) / sd
    zscores = zscores.fillna(0)
    matrix = zscores.to_numpy(dtype=float)
    details = np.empty(matrix.shape, dtype=object)
    for j, col in enumerate(raw.columns):
        for i in range(len(raw)):
            details[i, j] = (f"{raw.iloc[i, j]:,.0f} people" if col == "Population"
                              else f"{raw.iloc[i, j]:.2f} per 1,000")
    fig = go.Figure(go.Heatmap(
        z=matrix, x=list(raw.columns), y=list(raw.index), customdata=details,
        colorscale="RdBu", reversescale=True, zmid=0, zmin=-2.5, zmax=2.5,
        colorbar=dict(title="Z-score"),
        text=np.round(matrix, 1).astype(str), texttemplate="%{text}",
        hovertemplate="State: %{y}<br>Indicator: %{x}<br>Actual: %{customdata}<br>Z: %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(title=f"3. Standardized state comparison ({year}; within-indicator z-scores)",
                      xaxis_title="Indicator", yaxis_title="State", height=620)
    return fig

# END VISUALS

st.set_page_config(page_title="Malaysia Demography | JIE42403", page_icon="📊", layout="wide")

@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading latest OpenDOSM datasets...")
def load_live_data():
    # Unlike OpenAPI samples with limit=3, these links load the FULL official datasets.
    marriages_raw = pd.read_parquet(SOURCES["marriages"])
    births_raw = pd.read_parquet(SOURCES["births"])
    population_raw = pd.read_parquet(SOURCES["population"])
    return prepare_data(marriages_raw, births_raw, population_raw)

st.title("Malaysia Demographic Trends & Relationships")
st.caption("JIE42403 Scientific Visualisation")
st.markdown("**Study period:** 2017–2024 | **Sources:** OpenDOSM / DOSM, JPN")

try:
    df = load_live_data()
except Exception as exc:
    st.error("Could not load current OpenDOSM datasets. Check internet access and deployment logs.")
    st.exception(exc)
    st.stop()

states_all = sorted(df["state"].unique().tolist())
with st.sidebar:
    st.header("Filters")
    states = st.multiselect("Select states", states_all, default=states_all)
    focus_year = st.selectbox("Year for charts 2 and 3", list(range(END_YEAR, START_YEAR - 1, -1)))
    st.caption("Chart 1 always covers 2017–2024 for the selected states.")

if not states:
    st.warning("Select at least one state to display the charts.")
    st.stop()

focus = df.loc[df["year"].eq(focus_year) & df["state"].isin(states)]
col_a, col_b, col_c = st.columns(3)
col_a.metric("Female marriage registrations", f"{focus['female_marriages'].sum():,.0f}")
col_b.metric("Live births", f"{focus['live_births'].sum():,.0f}")
col_c.metric("Population", f"{focus['total_population'].sum():,.0f}")
st.caption(f"Summary counts refer to {focus_year} and the selected state(s); rates are not summed.")

st.divider()
st.subheader("Objective 1 — Trends")
st.write("Analyze changes in marriage registrations, live births and population between 2017 and 2024.")
st.plotly_chart(chart1_indexed_trends(df, states), use_container_width=True)
st.caption("Each indicator is indexed to its own 2017 baseline (100), allowing comparison of relative change, not absolute scale.")

st.divider()
st.subheader("Objective 2 — Relationships")
st.write("Examine the association between female marriage rates and crude birth rates across states, considering population size.")
fig, corr = chart2_population_bubbles(df, focus_year, states)
st.plotly_chart(fig, use_container_width=True)
st.caption(f"Pearson r = {corr:+.2f} for selected states ({focus_year}); bubble area indicates population. Association does not imply causation. The rates use different denominators.")

st.divider()
st.subheader("Objective 3 — State Comparison")
st.write("Compare marriage rates, crude birth rates and population across states using standardized values.")
st.plotly_chart(chart3_state_heatmap(df, focus_year, states), use_container_width=True)
st.caption("Z-scores are calculated separately for each indicator across selected states. Hover to see original units. These are relative positions, not rates of change.")

with st.expander("Data definitions, preprocessing, official source links"):
    st.markdown("""
- [Annual Marriages by State](https://open.dosm.gov.my/data-catalogue/marriages_state): female (`sex=female`) registrations and rates per 1,000 unmarried women.
- [Annual Live Births by State](https://open.dosm.gov.my/data-catalogue/births_annual_state): annual counts and crude birth rates per 1,000 residents, based on mother's state of residence.
- [Population Table: States](https://open.dosm.gov.my/data-catalogue/population_state): filter `sex=both`, `age=overall`, `ethnicity=overall` and multiply population (thousands) by 1,000.
- **Merge keys:** `state` and calendar `year`; fixed research interval 2017–2024, 16 states/Federal Territories, 128 rows.
- Rates have distinct denominators and should not be added or directly equated. The scatter plot is descriptive and pooled across states, not causal evidence.
- Original files are loaded live from OpenDOSM Parquet URLs, with a 24-hour Streamlit cache to reduce repeated downloads.
""")
