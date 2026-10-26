"""Shared data handling, styling and plotting helpers for the JIE42403 app."""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_FILE = Path(__file__).resolve().parent / 'data' / 'processed' / 'demography_merged_2017_2024.csv'
REQUIRED_COLUMNS = {
    'state', 'year', 'female_marriages', 'female_marriage_rate',
    'live_births', 'crude_birth_rate', 'total_population'
}
COLORS = px.colors.qualitative.Safe
PLOTLY_CONFIG = {'displaylogo': False, 'responsive': True, 'toImageButtonOptions': {'format': 'png', 'scale': 2}}


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f'Data file not found: {DATA_FILE}')
    df = pd.read_csv(DATA_FILE)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f'Missing expected CSV columns: {sorted(missing)}')
    if df.empty or df.duplicated(['state', 'year']).any() or df[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError('Dataset is empty or has missing/duplicate state-year records.')
    df['year'] = df['year'].astype(int)
    return df.sort_values(['state', 'year']).reset_index(drop=True)


def number(value: float) -> str:
    return f'{value:,.0f}'


def pct_change(first: float, last: float) -> str:
    if first == 0:
        return 'not available'
    return f'{(last / first - 1) * 100:+.1f}%'


def plot_style(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(
        template='plotly_white', height=height,
        margin=dict(l=12, r=12, t=45, b=15),
        font=dict(family='Arial, sans-serif', size=13, color='#203148'),
        title=dict(font=dict(size=18)),
        legend=dict(orientation='h', yanchor='top', y=-0.23, x=0, xanchor='left'),
        hovermode='closest',
    )
    fig.update_xaxes(showgrid=True, gridcolor='#E8EDF2', zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor='#E8EDF2', zeroline=False)
    return fig


def year_ticks(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(dtick=1, tickformat='d')
    return fig


def multi_line(df: pd.DataFrame, metric: str, title: str, ytitle: str) -> go.Figure:
    fig = px.line(
        df, x='year', y=metric, color='state', markers=True,
        color_discrete_sequence=COLORS, title=title,
        labels={'year': 'Year', metric: ytitle, 'state': 'State'},
        hover_data={metric: ':,.1f' if 'rate' in metric else ':,.0f', 'year': True},
    )
    fig.update_traces(line=dict(width=2.2), marker=dict(size=6))
    return year_ticks(plot_style(fig))


def scatter_relationship(df: pd.DataFrame) -> tuple[go.Figure, float]:
    fig = px.scatter(
        df, x='female_marriage_rate', y='crude_birth_rate', color='state',
        hover_data=['year', 'female_marriages', 'live_births'],
        color_discrete_sequence=COLORS,
        labels={
            'female_marriage_rate': 'Female marriage rate (per 1,000 unmarried women)',
            'crude_birth_rate': 'Crude birth rate (per 1,000 population)',
            'state': 'State',
        },
        title='Female Marriage Rate vs. Crude Birth Rate',
    )
    fig.update_traces(marker=dict(size=9, opacity=0.78))
    corr = df['female_marriage_rate'].corr(df['crude_birth_rate'])
    if len(df) >= 3 and df['female_marriage_rate'].nunique() > 1:
        slope, intercept = np.polyfit(df['female_marriage_rate'], df['crude_birth_rate'], 1)
        x = np.linspace(df['female_marriage_rate'].min(), df['female_marriage_rate'].max(), 100)
        fig.add_trace(go.Scatter(
            x=x, y=slope * x + intercept, mode='lines',
            line=dict(color='#263B53', width=3, dash='dash'), name='Pooled trend line',
        ))
    return plot_style(fig, height=480), float(corr) if pd.notna(corr) else float('nan')


def correlation_heatmap(df: pd.DataFrame) -> tuple[go.Figure, pd.DataFrame]:
    metrics = {
        'female_marriage_rate': 'Marriage rate',
        'crude_birth_rate': 'Birth rate',
        'total_population': 'Population',
    }
    corr = df[list(metrics)].rename(columns=metrics).corr()
    fig = px.imshow(
        corr, text_auto='.2f', aspect='auto', zmin=-1, zmax=1,
        color_continuous_scale='RdBu_r',
        title='Pearson Correlation (Selected State-Year Records)',
        labels={'color': 'Pearson r'},
    )
    fig.update_traces(hovertemplate='X: %{x}<br>Y: %{y}<br>Correlation: %{z:.2f}<extra></extra>')
    fig.update_layout(coloraxis_colorbar=dict(title='r'))
    return plot_style(fig, height=440), corr


def indexed_rates(df: pd.DataFrame, focus_state: str) -> tuple[go.Figure, pd.DataFrame]:
    subset = df[df.state.eq(focus_state)].sort_values('year').copy()
    first = subset.iloc[0]
    subset['Marriage rate index'] = subset['female_marriage_rate'] / first['female_marriage_rate'] * 100
    subset['Birth rate index'] = subset['crude_birth_rate'] / first['crude_birth_rate'] * 100
    melted = subset.melt(
        id_vars='year', value_vars=['Marriage rate index', 'Birth rate index'],
        var_name='Series', value_name='Index',
    )
    fig = px.line(
        melted, x='year', y='Index', color='Series', markers=True,
        color_discrete_sequence=['#1D9A95', '#D97757'],
        labels={'year': 'Year', 'Index': 'Index (first selected year = 100)'},
        title=f'Indexed Rate Changes — {focus_state}',
    )
    fig.add_hline(y=100, line=dict(color='#8792A2', dash='dot', width=1))
    return year_ticks(plot_style(fig)), subset


def ranked_births(df: pd.DataFrame, year: int) -> go.Figure:
    current = df[df.year.eq(year)].sort_values('crude_birth_rate')
    fig = px.bar(
        current, y='state', x='crude_birth_rate', orientation='h',
        color='crude_birth_rate', color_continuous_scale='Tealgrn',
        labels={'state': 'State', 'crude_birth_rate': 'Live births per 1,000 people'},
        title=f'Crude Birth Rate Ranking — {year}', text='crude_birth_rate',
    )
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside', cliponaxis=False)
    fig.update_layout(coloraxis_showscale=False, showlegend=False)
    return plot_style(fig, height=max(370, 45 * len(current) + 95))


def marriages_heatmap(df: pd.DataFrame) -> go.Figure:
    matrix = df.pivot(index='state', columns='year', values='female_marriage_rate')
    fig = px.imshow(
        matrix, color_continuous_scale='YlGnBu', aspect='auto',
        labels={'x': 'Year', 'y': 'State', 'color': 'Marriage rate'},
        title='Female Marriage Rate by State and Year',
    )
    fig.update_traces(hovertemplate='State: %{y}<br>Year: %{x}<br>Rate: %{z:.1f}<extra></extra>')
    return plot_style(fig, height=max(400, len(matrix) * 39 + 130))


def bubble_states(df: pd.DataFrame, year: int) -> go.Figure:
    current = df[df.year.eq(year)].copy()
    current['Population (millions)'] = current['total_population'] / 1_000_000
    fig = px.scatter(
        current, x='Population (millions)', y='crude_birth_rate',
        size='female_marriage_rate', color='state', size_max=42,
        hover_data={
            'female_marriage_rate': ':.1f',
            'total_population': ':,.0f',
            'live_births': ':,.0f',
            'Population (millions)': ':.2f',
        },
        labels={'crude_birth_rate': 'Live births per 1,000 people',
                'state': 'State', 'female_marriage_rate': 'Marriage rate'},
        color_discrete_sequence=COLORS,
        title=f'Population, Birth Rate and Marriage Rate — {year}',
    )
    return plot_style(fig, height=475)


def show_chart(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key=key)


def report_footer() -> None:
    st.divider()
    with st.expander('Data definitions, methodology and sources'):
        st.markdown('''
**Unit of observation:** One state (including Federal Territories) in one year, 2017–2024 (128 records total).

- **Female marriages:** Marriage registrations for women resident in the state; male and female counts are **not** added.
- **Female marriage rate:** Registrations per 1,000 unmarried women, using OpenDOSM's published denominator.
- **Live births:** Registered live births by mother's state of residence.
- **Crude birth rate:** Registered live births per 1,000 of the total population.
- **Total population:** Original OpenDOSM population figures were in thousands and were multiplied by 1,000.

**Interpretation cautions:** Marriage and birth rates have different denominators; neither should be summed across states. Correlations across state-year observations are descriptive and do not establish causation. A birth in one year need not relate to a marriage in that same year. Population totals can contain estimation/revision effects.

**Original open data (OpenDOSM):**
- [Annual marriages by state](https://open.dosm.gov.my/data-catalogue/marriages_state)
- [Annual live births by state](https://open.dosm.gov.my/data-catalogue/births_annual_state)
- [Population table: states](https://open.dosm.gov.my/data-catalogue/population_state)

**Method:** Filter 2017–2024; select female marriage records; keep total population (`sex=both`, `age=overall`, `ethnicity=overall`); merge on `state` and `year`. Correlation uses Pearson's r, pooled across selected state-year observations.
''')
