import os
from pathlib import Path
import pandas as pd
import streamlit as st
import db, pipeline, support, advisor

st.set_page_config(page_title="AI & Automation Service Desk", page_icon="🛠️", layout="wide")

pw = os.environ.get("APP_PASSWORD")
if pw and st.text_input("Password", type="password") != pw:
    st.stop()

db.seed_if_empty()

st.title("🛠️ AI & Automation Service Desk")
st.caption("Synthetic demo: support, discovery, delivery and continuous improvement for AI and process automation.")

tab_support, tab_adv, tab_claims, tab_metrics = st.tabs(
    ["💬 AI Support", "🔍 Automation Advisor", "📨 Claims automation", "📈 Service metrics"])

with tab_support:
    st.subheader("Ask the AI Support Desk")
    q = st.text_input("Question", placeholder="e.g. Can I paste a customer's policy number into a public AI tool?")
    if st.button("Ask", type="primary") and q.strip():
        st.session_state["last"] = support.ask(q.strip())
    rec = st.session_state.get("last")
    if rec:
        if rec["escalated"]:
            st.warning("Escalated to the AI Support team (no reliable answer in the knowledge base).")
        st.write(rec["answer"])
        if rec["sources"]:
            st.caption("Sources: " + " · ".join(rec["sources"]))
        c1, c2, _ = st.columns([1, 1, 8])
        if c1.button("👍", key="up"):
            db.set_feedback(rec["id"], "up")
            st.toast("Thanks for the feedback")
        if c2.button("👎", key="down"):
            db.set_feedback(rec["id"], "down")
            st.toast("Thanks, this helps improve the knowledge base")

with tab_adv:
    st.subheader("Describe a manual process")
    ex = st.selectbox("Load an example", ["(write your own)"] + list(advisor.EXAMPLES))
    title = st.text_input("Process name", value=ex if ex in advisor.EXAMPLES else "", key=f"t_{ex}")
    desc = st.text_area("Description (volume and time per case help the scoring)",
                        value=advisor.EXAMPLES.get(ex, ""), height=150, key=f"d_{ex}")
    if st.button("Assess", type="primary") and desc.strip():
        st.session_state["assessment"] = advisor.assess(title or "Untitled process", desc)
    r = st.session_state.get("assessment")
    if r:
        a, s = r["assessment"], r["score"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Approach", a["recommended_approach"])
        m2.metric("Manual effort / month", f"{s['manual_hours']} h" if s["manual_hours"] is not None else "unknown")
        m3.metric("Feasibility", f"{s['feasibility']}/10")
        m4.metric("Priority", f"{s['priority']} ({s['label']})")
        st.markdown(r["brief"])

ICON = {"standard_queue": "🟢", "senior_review": "🟠", "fraud_review": "🔴",
        "policy_issue": "🟣", "request_more_info": "🟡", "manual_review": "⚪"}

with tab_claims:
    st.subheader("Reference solution: claims intake automation")
    st.caption("LLM extraction → tool-calling verification → rule-based routing → human approval.")
    Path("inbox").mkdir(exist_ok=True)
    for f in st.file_uploader("Upload claim emails (.txt, .pdf)", type=["txt", "pdf"],
                              accept_multiple_files=True) or []:
        Path("inbox", f.name).write_bytes(f.getvalue())
    b1, b2, _ = st.columns([1, 1, 5])
    if b1.button("Process inbox", type="primary"):
        done = {c["source_file"] for c in db.all_claims()}
        files = sorted(p for p in Path("inbox").iterdir()
                       if p.suffix in (".txt", ".pdf") and p.name not in done)
        if files:
            bar = st.progress(0.0)
            for i, p in enumerate(files):
                pipeline.process(p)
                bar.progress((i + 1) / len(files))
        st.rerun()
    if b2.button("Reset to sample data"):
        db.reset()
        db.seed_if_empty()
        st.rerun()

    claims = db.all_claims()
    if not claims:
        st.info("Nothing here yet. Click 'Process inbox'.")
    else:
        st.dataframe(pd.DataFrame([{
            "id": c["id"], "file": c["source_file"],
            "action": f"{ICON[c['action']]} {c['action']}", "status": c["status"],
            "amount_eur": c["claim"].get("estimated_amount_eur"),
            "urgency": c["claim"].get("urgency")} for c in claims]),
            hide_index=True)
        by_id = {c["id"]: c for c in claims}
        pick_id = st.selectbox("Review a claim", list(by_id), format_func=lambda i:
                               f"#{i} · {by_id[i]['source_file']} · {by_id[i]['action']}")
        pick = by_id[pick_id]
        left, right = st.columns(2)
        with left:
            st.markdown("**Extracted data**")
            st.json(pick["claim"])
            for why in pick["reasons"]:
                st.warning(why)
            if pick["payout"] is not None:
                st.metric("Estimated payout (after deductible)", f"€{pick['payout']:,.0f}")
            with st.expander("Agent tool trace"):
                st.json(pick["trace"])
        with right:
            st.markdown("**Draft reply (editable)**")
            text = st.text_area("Reply", pick["draft"], height=260, key=f"d{pick['id']}")
            a1, a2 = st.columns(2)
            if a1.button("Approve", key=f"a{pick['id']}"):
                db.set_status(pick["id"], "approved", text)
                st.rerun()
            if a2.button("Reject", key=f"r{pick['id']}"):
                db.set_status(pick["id"], "rejected", text)
                st.rerun()
            st.caption(f"Status: {pick['status']}")


with tab_metrics:
    sup = pd.DataFrame(db.all_support())
    reqs = db.all_requests()
    claims = db.all_claims()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Support questions", len(sup))
    m2.metric("Escalation rate", f"{sup.escalated.mean():.0%}" if len(sup) else "-")
    rated = sup[sup.feedback.notna()] if len(sup) else sup
    m3.metric("Rated helpful", f"{(rated.feedback == 'up').mean():.0%}" if len(rated) else "-")
    m4.metric("Automation requests", len(reqs))

    if len(sup) and sup.escalated.sum():
        st.subheader("Knowledge gaps (escalated questions)")
        st.dataframe(sup[sup.escalated == 1][["created_at", "question"]], hide_index=True)
    if reqs:
        st.subheader("Automation backlog by priority")
        st.dataframe(pd.DataFrame([{
            "request": r["title"], "approach": r["assessment"]["recommended_approach"],
            "manual_h_per_month": r["manual_hours"], "priority": r["priority"],
            "label": r["priority_label"]} for r in reqs]).sort_values("priority", ascending=False),
            hide_index=True)
    if claims:
        st.subheader("Claims automation")
        st.bar_chart(pd.DataFrame(claims).action.value_counts())