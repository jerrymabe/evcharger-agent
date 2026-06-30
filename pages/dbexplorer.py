import streamlit as st
import pandas as pd
import altair as alt
import pandas as pd
import config as settings
import sqlite3

@st.cache_data
def read_sql_table(table_name):
    # conn = st.connection('evc_db', type='sql')
    # data = conn.query('select * from '+table_name)
    sql_query = 'select * from '+table_name
    conn = sqlite3.connect(settings.DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    df = pd.read_sql_query(sql_query, conn)
    df = df.astype(str)
    if table_name == 'dp_ast':
        df = df.set_index("techincal_indent_num")
    elif table_name == 'evc_dvc_sts' or table_name == 'evc_flt':
        df = df.set_index('ast_id')
    elif table_name == 'evc_maintenance':
        df = df.set_index('ccl_num')
    else:
        df = df.set_index('ev_charger_num')
    return df

st.set_page_config(page_title="DB Explorer", page_icon="📊")
st.markdown("# Database Explorer")
st.sidebar.header("List of Tables")
st.write("""Here, you can query the tables and see the data for yourself!""")
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem; /* Adjust this value as needed */
    }
    ul[data-testid="stSidebarNavItems"] {
        padding-top: 3rem; /* Adjust this value as needed */
    }
    div.stButton > button {
        border-radius: 20px;     /* pill shape */
        padding: 6px 18px;
    }
    </style>
    """, unsafe_allow_html=True)

if "df" not in st.session_state:
    st.session_state.df = None
    st.session_state.text = None

if st.sidebar.button("Charger Details"):
    st.session_state.text = "Charger Details"
    st.session_state.df = read_sql_table('dp_ast')
if st.sidebar.button("Charger Status"):
    st.session_state.text = "Charger Status"
    st.session_state.df = read_sql_table('evc_dvc_sts')
if st.sidebar.button("Charger Notifications"):
    st.session_state.text = "Charger Notifications"
    st.session_state.df = read_sql_table('evc_notifications')
if st.sidebar.button("Charger Maintenance"):
    st.session_state.text = "Charger Maintenance"
    st.session_state.df = read_sql_table('evc_maintenance')
if st.sidebar.button("Charger Faults"):
    st.session_state.text = "Charger Faults"
    st.session_state.df = read_sql_table('evc_flt')

data = None
if st.session_state.df is not None:
    df = st.session_state.df
    if st.session_state.text != 'Charger Notifications':
        assets = st.multiselect(
            "Choose asset", list(df.index), []
        )
    else:
        assets = st.multiselect(
            "Choose asset", list(df.index), []
        )
    if assets:
        data = df.loc[assets]
        st.write("### "+st.session_state.text, data.sort_index())

    else:
        data = df
        st.write("### "+st.session_state.text, data.sort_index())

    chart = None
    if st.session_state.text == "Charger Details":
        category_counts = df.groupby(["mtrl", "usr_sts_lbl"]).size().reset_index(name="count")
        chart = (
            alt.Chart(category_counts)
            .mark_bar()
            .encode(
                x=alt.X("mtrl:N", title="Type of Charger"),
                y=alt.Y("count:Q", title="Number of Chargers"),
                color="usr_sts_lbl:N",
                tooltip=["usr_sts_lbl", "mtrl", "count"]
            )
        )
    elif st.session_state.text == "Charger Status":
        category_counts = df["devicestatus"].value_counts().reset_index()
        category_counts.columns = ["devicestatus", "count"]
        chart = (
            alt.Chart(category_counts)
            .mark_bar()
            .encode(
                x=alt.X("devicestatus:N", title="Status of Charger"),
                y=alt.Y("count:Q", title="Number of Chargers"),
                color="devicestatus:N",
                tooltip=["devicestatus", "count"]
            )
        )
    elif st.session_state.text == "Charger Notifications":
        status_notif_counts = df.groupby(["ntfn_usts_lbl", "ntfn_type"]).size().reset_index(name="count")
        chart = (
            alt.Chart(status_notif_counts)
            .mark_bar()
            .encode(
                x=alt.X("ntfn_usts_lbl:N", title="Status"),
                y=alt.Y("count:Q", title="Number of Notifications"),
                color="ntfn_type:N",
                tooltip=["ntfn_usts_lbl", "ntfn_type", "count"]
            )
            .properties(
                height=600
            )
        )
    elif st.session_state.text == "Charger Maintenance":
        df["year"] = df["last_mnt_dt"].str[:4]
        year_counts = df["year"].value_counts().reset_index()
        year_counts.columns = ["year", "count"]
        chart = (
            alt.Chart(year_counts)
            .mark_arc()
            .encode(
                theta="count:Q",      # slice size
                color="year:N",       # slice color
                tooltip=["year", "count"]
            )
            .properties(
                title="Last Maintenance Year of Chargers"   # 👈 Add your title here
            )
            .configure_title(
                anchor="middle",   # 👈 Center align
                fontSize=16,       # (optional) adjust size
                fontWeight="normal"
            )
        )
    elif st.session_state.text == "Charger Faults":
        df["time"] = pd.to_datetime(df["created_date"], errors="coerce")
        df = df.dropna(subset=["time"])
        df = df.reset_index()
        agg_df = df.groupby(["ast_id", "time"], as_index=False)["err"].count()

        chart = (
            alt.Chart(agg_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("time:T", title="Time"),
                y=alt.Y("err:Q", title="Number of Faults"),
                color="ast_id:N",      # one line per item
                tooltip=["ast_id", "time", "err"]
            )
            .properties(
                height=700,
                title="Failures Over Time by Item"
            )
        )

    if chart:
        st.altair_chart(chart, use_container_width=True)
