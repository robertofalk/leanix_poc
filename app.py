from zoneinfo import ZoneInfo
import streamlit as st
from enrichment.enrichment import Enrichment

@st.cache_resource
def enrichment():
    return Enrichment()

def show(data):
    st.text_area("Description", data.description)
    st.text_input("Provider", data.provider)
    st.text_input("Status", data.lifeciycle_status)

    if data.new_name:
        st.text_input("New name", data.new_name)

    with st.expander("Details"):
        local_time = data.last_update.astimezone(ZoneInfo('Europe/Berlin')).strftime("%d.%m.%Y %H:%M:%S")
        st.text_input("Last Update", local_time)
        st.text_input("Revision", data.revision)
        st.text_input("Source", data.source)
        st.text_input("Meteor Score", data.meteor_score)
        st.text_area("Reference", data.ref_text, height=200)
        

st.set_page_config(
    page_title="Enrichment",
    page_icon="🤖",
    initial_sidebar_state='collapsed' if 'sidebar_state' not in st.session_state else st.session_state.sidebar_state)
st.title("Enrichment")


with st.sidebar.container(border=True):

    jobs = enrichment().get_job_status()
    if not jobs:
        st.write("Job status: STOPPED")
        ignore_revisions = st.checkbox("Ignore revisions", key="ignore_revisions")
        btn_start = st.button("Start job")

        if btn_start:
            enrichment().start_job(ignore_revisions=ignore_revisions)
            st.rerun()
    else:
        st.write("Job status: RUNNING")
        local_time = jobs[0].next_run_time.astimezone(ZoneInfo('Europe/Berlin')).strftime("%d.%m.%Y %H:%M:%S")
        
        st.write("Next run:", local_time)
        btn_stop = st.button("Stop job")
        if btn_stop:
            enrichment().stop_job()
            st.rerun()

with st.sidebar.expander("Database operations"):
    with st.form("form", clear_on_submit=True, border=False):
        entry = st.text_input("Entry")
        btn_delete = st.form_submit_button('Delete')
        
        if btn_delete:
            enrichment().delete(entry)
            st.success("Entry deleted successfully.")

    btn_delete_all = st.button("Delete all", type="primary")
    if btn_delete_all:
        enrichment().delete()
        st.success("Database cleaned successfully.")


st.write("This web application works as an interface to the enrichment functionality.")

with st.form("entity_form", clear_on_submit=False):
    left, middle, right = st.columns(3, vertical_alignment="bottom")

    name = left.text_input("Application or IT component name", placeholder="i.e. Windows XP")
    # btn_enrich = middle.button("Enrich", type="primary", use_container_width=True)
    btn_enrich = middle.form_submit_button("Enrich", type="primary", use_container_width=True)
    btn_get = right.form_submit_button("Read")

    if btn_enrich:
        with st.spinner(text=f"Enriching {name}..."):
            try:
                data = enrichment().enrich(name)
                show(data)
            except RuntimeError as error:
                st.warning(str(error))

    if btn_get:
        with st.spinner(text=f"Reading {name}..."):
            try:
                data = enrichment().read(name)
                show(data)
            except RuntimeError as error:
                st.warning(str(error))