"""Run: streamlit run app.py | Deployed entrypoint: app.py."""
import streamlit as st
from shared import load_data

st.set_page_config(
    page_title='Malaysia Demographic Explorer | JIE42403',
    page_icon='📊', layout='wide', initial_sidebar_state='expanded',
)

st.markdown('''<style>
.block-container {max-width: 1280px; padding-top: 1.7rem; padding-bottom: 3rem;}
h1 {font-weight: 760 !important; letter-spacing: -.025em;}
h2,h3 {letter-spacing: -.015em;}
[data-testid="stMetric"] {background:#F3F7FA; padding:15px 19px; border-radius:12px; border:1px solid #E5ECF3;}
[data-testid="stMetricLabel"] {font-size:.93rem;}
</style>''', unsafe_allow_html=True)

try:
    data = load_data()
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.info('Place the cleaned CSV at data/processed/demography_merged_2017_2024.csv, then rerun the app.')
    st.stop()

st.sidebar.title('Malaysia Demographic Explorer')
st.sidebar.caption('JIE42403 • Scientific Visualisation')
st.sidebar.divider()

states = sorted(data['state'].unique().tolist())
selected_states = st.sidebar.multiselect(
    'States / Federal Territories', options=states, default=states,
    help='Select one or more states. All 16 are selected initially.',
)
years = (int(data['year'].min()), int(data['year'].max()))
start_year, end_year = st.sidebar.slider(
    'Year range', min_value=years[0], max_value=years[1],
    value=years, step=1,
)
if not selected_states:
    st.warning('Choose at least one state in the sidebar to continue.')
    st.stop()

filtered = data.loc[
    data['state'].isin(selected_states) & data['year'].between(start_year, end_year)
].copy()
available_years = sorted(filtered['year'].unique().tolist(), reverse=True)
comparison_year = st.sidebar.selectbox(
    'Page 3: comparison year', options=available_years, index=0,
    help='The ranking and bubble chart compare states for one year.',
)
focus_state = st.sidebar.selectbox(
    'Page 2: indexed-trends state', options=sorted(selected_states), index=0,
)
st.sidebar.caption(f'{len(selected_states)} states · {start_year}–{end_year} · {len(filtered)} records')
st.sidebar.download_button(
    label='Download filtered CSV',
    data=filtered.to_csv(index=False).encode('utf-8'),
    file_name='filtered_demography.csv', mime='text/csv',
    use_container_width=True,
)
st.sidebar.divider()
st.sidebar.caption('Source: Department of Statistics Malaysia (OpenDOSM)')

# Make the common filters available to all three Streamlit pages.
st.session_state['filtered_data'] = filtered
st.session_state['comparison_year'] = comparison_year
st.session_state['focus_state'] = focus_state
st.session_state['year_range'] = (start_year, end_year)

pages = [
    st.Page('pages/1_Demographic_Trends.py', title='1 · Demographic Trends', icon='📈', default=True),
    st.Page('pages/2_Relationship_Analysis.py', title='2 · Relationship Analysis', icon='🔎'),
    st.Page('pages/3_State_Comparison.py', title='3 · State Comparison', icon='🗺️'),
]
nav = st.navigation(pages, position='sidebar')
nav.run()
