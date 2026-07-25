from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from app.services.application_context import get_selected_job, save_selected_job
from app.services.application_queue import add_jobs_to_queue, export_queue_csv, get_active_queue, load_queue, queue_summary, remove_queue_item, update_queue_item
from app.services.job_repository import get_saved_jobs

st.set_page_config(page_title="CareerPilot Auto Apply Assistant", page_icon="⚡", layout="wide")
st.title("⚡ Auto Apply Assistant")
st.caption("Build a high-priority application queue, prepare each application, open the official job page, and track what you applied to.")
st.warning("CareerPilot does not submit applications automatically. You must review every resume, message, and application before submitting.")

selected_job = get_selected_job(st.session_state)
saved_jobs = get_saved_jobs()
queue = load_queue()
summary = queue_summary(queue)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Queue Total", summary["total"])
m2.metric("Ready", summary["ready"])
m3.metric("Applied", summary["applied"])
m4.metric("Skipped", summary["skipped"])

tab1, tab2, tab3 = st.tabs(["Build Queue", "Application Queue", "History & Export"])

with tab1:
    st.subheader("Add Jobs to the Application Queue")
    if selected_job:
        st.success(f"Current selected job: {selected_job.get('job_role') or 'Unknown Role'} at {selected_job.get('company') or 'Unknown Company'}")
        if st.button("Add Current Selected Job", type="primary", width="stretch"):
            result = add_jobs_to_queue([selected_job])
            st.success("Selected job added to the queue." if result["added"] else "This job is already in the queue.")
            st.rerun()
    else:
        st.info("No job is currently selected. Open Job Search and click Prepare Application.")

    st.divider()
    st.subheader("Add from Saved Jobs")
    if not saved_jobs:
        st.info("No saved jobs are available.")
    else:
        labels = []
        label_to_job = {}
        for index, job in enumerate(saved_jobs):
            role = job.get("role") or job.get("title") or "Unknown Role"
            company = job.get("company") or "Unknown Company"
            score = int(float(job.get("match_score") or 0))
            label = f"{score}% - {role} at {company} [{index + 1}]"
            labels.append(label)
            label_to_job[label] = job
        selected_labels = st.multiselect("Select saved jobs", options=labels)
        if st.button("Add Selected Saved Jobs", width="stretch", disabled=not selected_labels):
            result = add_jobs_to_queue([label_to_job[label] for label in selected_labels])
            st.success(f"Added {result['added']} job(s). Skipped {result['duplicates']} duplicate(s).")
            st.rerun()

with tab2:
    st.subheader("High-Priority Application Queue")
    active_queue = get_active_queue(queue)
    if not active_queue:
        st.info("Your active application queue is empty.")
    else:
        for position, item in enumerate(active_queue, start=1):
            with st.expander(f"#{position} - {item.get('match_score', 0)}% - {item.get('role')} at {item.get('company')}"):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Status:** {item.get('status')}")
                c1.write(f"**Priority:** {item.get('priority') or 'Review'}")
                c2.write(f"**Location:** {item.get('location') or 'Not provided'}")
                c2.write(f"**Source:** {item.get('source') or 'Not provided'}")
                c3.write(f"**Freshness:** {item.get('freshness_label') or 'Unknown'}")
                c3.write(f"**Timing:** {item.get('apply_urgency') or 'Review normally'}")
                st.write(f"**Matched skills:** {item.get('matched_skills') or 'Not available'}")
                st.write(f"**Missing skills:** {item.get('missing_skills') or 'None detected'}")
                st.write(f"**Recommended resume:** {item.get('resume_version') or 'Data Analyst Resume'}")

                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("Prepare Application", key=f"prepare_{item['queue_id']}", type="primary", width="stretch"):
                        save_selected_job(st.session_state, {
                            "title": item["role"], "company": item["company"], "location": item["location"],
                            "job_url": item["job_link"], "description": item["job_description"], "site": item["source"],
                            "match_score": item["match_score"], "priority": item["priority"], "apply_urgency": item["apply_urgency"],
                            "matched_skills": item["matched_skills"], "missing_skills": item["missing_skills"],
                            "resume_version": item["resume_version"],
                        })
                        update_queue_item(item["queue_id"], status="Ready to Apply")
                        st.switch_page("pages/2_Apply_Workflow.py")
                with b2:
                    if item.get("job_link"):
                        st.link_button("Open Job", item["job_link"], width="stretch")
                    else:
                        st.button("Open Job", disabled=True, key=f"open_disabled_{item['queue_id']}", width="stretch")
                with b3:
                    if st.button("Mark Applied", key=f"applied_{item['queue_id']}", width="stretch"):
                        update_queue_item(item["queue_id"], status="Applied")
                        st.success("Application marked as applied.")
                        st.rerun()
                with b4:
                    if st.button("Skip", key=f"skip_{item['queue_id']}", width="stretch"):
                        update_queue_item(item["queue_id"], status="Skipped")
                        st.rerun()

                notes = st.text_area("Application notes", value=item.get("notes", ""), key=f"notes_{item['queue_id']}")
                n1, n2 = st.columns(2)
                with n1:
                    if st.button("Save Notes", key=f"save_notes_{item['queue_id']}", width="stretch"):
                        update_queue_item(item["queue_id"], notes=notes)
                        st.success("Notes saved.")
                with n2:
                    if st.button("Remove from Queue", key=f"remove_{item['queue_id']}", width="stretch"):
                        remove_queue_item(item["queue_id"])
                        st.rerun()

with tab3:
    st.subheader("Application Queue History")
    queue = load_queue()
    if not queue:
        st.info("No application queue history yet.")
    else:
        history_df = pd.DataFrame(queue)
        cols = ["match_score", "company", "role", "location", "status", "priority", "source", "added_at", "applied_at", "notes"]
        st.dataframe(history_df[[c for c in cols if c in history_df.columns]], width="stretch", hide_index=True)
        export_path = Path(export_queue_csv(queue=queue))
        st.download_button("Download Application Queue CSV", data=export_path.read_bytes(), file_name=export_path.name, mime="text/csv", width="stretch")
