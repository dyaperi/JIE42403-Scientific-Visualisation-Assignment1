"""Objective 1: trends in counts and population."""
import plotly.express as px
import streamlit as st
from shared import multi_line, number, pct_change, plot_style, report_footer, show_chart, year_ticks

st.title('1 · Demographic Trends')
st.markdown('**Objective 1:** To analyze trends in female marriage registrations, live births, and population across Malaysian states from 2017 to 2024.')

df = st.session_state['filtered_data']
years = sorted(df['year'].unique())
by_year = df.groupby('year', as_index=False).agg(
    female_marriages=('female_marriages', 'sum'),
    live_births=('live_births', 'sum'),
    total_population=('total_population', 'sum'),
)
latest = by_year.iloc[-1]

m1, m2, m3, m4 = st.columns(4)
m1.metric('Female marriages (selected period)', number(df['female_marriages'].sum()))
m2.metric('Live births (selected period)', number(df['live_births'].sum()))
m3.metric(f'Population ({int(latest.year)})', number(latest.total_population))
m4.metric('States / years', f'{df.state.nunique()} / {len(years)}')

st.subheader('Chart 1 · Female marriage registrations')
show_chart(multi_line(df, 'female_marriages', 'Annual Female Marriages by State', 'Female marriage registrations'), 'trends_marriages')
start, end = by_year.iloc[0], by_year.iloc[-1]
st.info(f'Across the selected states, female marriage registrations were {number(start.female_marriages)} in {int(start.year)} and {number(end.female_marriages)} in {int(end.year)} (change: {pct_change(start.female_marriages, end.female_marriages)}). Compare individual lines to see which states drive the pattern.')

st.subheader('Chart 2 · Annual live births')
show_chart(multi_line(df, 'live_births', 'Annual Live Births by State', 'Live births'), 'trends_births')
st.info(f'Annual live births in the selected states changed from {number(start.live_births)} in {int(start.year)} to {number(end.live_births)} in {int(end.year)} (change: {pct_change(start.live_births, end.live_births)}). This is a change in *counts*, not necessarily birth rates.')

st.subheader('Chart 3 · Combined selected-state population')
fig = px.area(
    by_year, x='year', y='total_population',
    title='Total Population in the Selected States',
    labels={'year': 'Year', 'total_population': 'Population (people)'},
    color_discrete_sequence=['#238A94'],
)
fig.update_traces(line=dict(width=2.5))
show_chart(year_ticks(plot_style(fig)), 'trends_population')
st.info(f'Combined population changed from {number(start.total_population)} in {int(start.year)} to {number(end.total_population)} in {int(end.year)} (change: {pct_change(start.total_population, end.total_population)}). The shaded area is a **sum of the selected state populations**, not the population of each state separately.')

report_footer()
