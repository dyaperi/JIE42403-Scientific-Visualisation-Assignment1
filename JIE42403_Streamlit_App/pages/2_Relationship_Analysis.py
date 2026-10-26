"""Objective 2: descriptive associations between marriage, birth and population."""
import numpy as np
import streamlit as st
from shared import correlation_heatmap, indexed_rates, number, report_footer, scatter_relationship, show_chart

st.title('2 · Relationship Analysis')
st.markdown('**Objective 2:** To examine descriptive statistical relationships among female marriage rates, crude birth rates, and population across selected Malaysian state-year records.')
df = st.session_state['filtered_data']
focus = st.session_state['focus_state']

fig_scatter, r = scatter_relationship(df)
a, b, c = st.columns(3)
a.metric('State-year observations', number(len(df)))
b.metric('Pearson r: marriage vs birth rate', f'{r:+.2f}' if np.isfinite(r) else 'N/A')
c.metric('States represented', str(df.state.nunique()))

st.subheader('Chart 4 · Rate relationship scatter plot')
show_chart(fig_scatter, 'relation_scatter')
if np.isfinite(r):
    descriptor = 'positive' if r > 0 else 'negative' if r < 0 else 'near-zero'
    st.info(f'The selected observations show a {descriptor} pooled Pearson correlation (r = {r:+.2f}, n = {len(df)}). The dashed line is a descriptive fit; it does not establish that changes in marriage registrations cause changes in births. Repeated observations from states and common year trends may affect the relationship.')
else:
    st.info('There is insufficient variability to calculate a meaningful correlation for the chosen filters.')

st.subheader('Chart 5 · Correlation heatmap')
fig_heat, corr = correlation_heatmap(df)
show_chart(fig_heat, 'relation_heatmap')
st.info('The heatmap summarizes linear correlations across the filtered state-year records. Population may correlate with rates because states differ in size and composition; interpreting these as causal relationships would be inappropriate.')
if len(df) < 3:
    st.caption('Very small selections may not yield stable or computable correlations. Select more years or states for this chart.')

st.subheader('Chart 6 · Indexed rate trends for one state')
fig_index, focus_data = indexed_rates(df, focus)
show_chart(fig_index, 'relation_indexed')
first, last = focus_data.iloc[0], focus_data.iloc[-1]
st.info(f'For **{focus}**, the female marriage rate index moved from 100 to {last["Marriage rate index"]:.1f}, while the crude birth rate index moved from 100 to {last["Birth rate index"]:.1f} between {int(first.year)} and {int(last.year)}. Each index uses the **first selected year = 100**; it compares proportional changes, not rate levels or denominators.')
if df.year.nunique() == 1:
    st.caption('Select at least two years to see changes over time in Chart 6.')

report_footer()
