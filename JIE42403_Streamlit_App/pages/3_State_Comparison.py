"""Objective 3: compare state patterns, rates and population."""
import streamlit as st
from shared import bubble_states, marriages_heatmap, number, ranked_births, report_footer, show_chart

st.title('3 · State Comparison')
st.markdown('**Objective 3:** To compare demographic differences among Malaysian states using annual crude birth rates, female marriage rates, and population size.')
df = st.session_state['filtered_data']
year = st.session_state['comparison_year']
current = df[df.year.eq(year)].copy()
max_birth = current.loc[current['crude_birth_rate'].idxmax()]
min_birth = current.loc[current['crude_birth_rate'].idxmin()]
max_pop = current.loc[current['total_population'].idxmax()]

m1, m2, m3 = st.columns(3)
m1.metric('Highest crude birth rate', f'{max_birth.crude_birth_rate:.1f}', max_birth.state, delta_color='off')
m2.metric('Lowest crude birth rate', f'{min_birth.crude_birth_rate:.1f}', min_birth.state, delta_color='off')
m3.metric('Largest population', number(max_pop.total_population), max_pop.state, delta_color='off')

st.subheader('Chart 7 · Birth-rate ranking')
show_chart(ranked_births(df, year), 'compare_rank')
st.info(f'In {year}, **{max_birth.state}** had the highest crude birth rate among the selected states ({max_birth.crude_birth_rate:.1f} births per 1,000 people), while **{min_birth.state}** had the lowest ({min_birth.crude_birth_rate:.1f}). This is a comparison of rates, not absolute birth counts.')

st.subheader('Chart 8 · Marriage-rate heatmap')
show_chart(marriages_heatmap(df), 'compare_heatmap')
peak = df.loc[df['female_marriage_rate'].idxmax()]
st.info(f'The highest female marriage rate in the selected state-year data was {peak.female_marriage_rate:.1f} per 1,000 unmarried women in **{peak.state} ({int(peak.year)})**. Color intensity helps identify year-to-year and state-level patterns.')

st.subheader('Chart 9 · Population and demographic rates')
show_chart(bubble_states(df, year), 'compare_bubbles')
r = current['total_population'].corr(current['crude_birth_rate']) if len(current) > 2 else float('nan')
if len(current) > 2 and r == r:
    st.info(f'For {year}, the across-state correlation between population size and crude birth rate is r = {r:+.2f} for the selected states. Each bubble is one state; its **area** represents female marriage rate. Larger populations do not automatically imply higher birth rates.')
else:
    st.info('Select at least three states with varying populations to inspect their descriptive correlation.')

report_footer()
