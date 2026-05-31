import streamlit as st
import uuid, json, os, re
from datetime import datetime
from urllib.parse import quote_plus

# --- SYSTEM CONFIG ---
FILES = {"queue": "queue_data.json", "survey": "survey_log.json"}

def load_data(f, d):
    try:
        if os.path.exists(f):
            with open(f, 'r', encoding='utf-8') as fh:
                return json.load(fh)
    except Exception:
        return d
    return d

def save_data(f, d):
    tmp = f + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, indent=4, ensure_ascii=False)
    try:
        os.replace(tmp, f)
    except Exception:
        # best-effort fallback
        os.remove(tmp)

if 'queue' not in st.session_state: st.session_state.queue = load_data(FILES["queue"], [])
if 'delete_idx' not in st.session_state: st.session_state.delete_idx = None
if 'last_ticket' not in st.session_state: st.session_state.last_ticket = None
if 'edit_idx' not in st.session_state: st.session_state.edit_idx = None
if 'last_entry_notice' not in st.session_state: st.session_state.last_entry_notice = None

SURVEY_BASE_URL = os.environ.get("SURVEY_BASE_URL", "").rstrip("/")
if not SURVEY_BASE_URL:
    SURVEY_BASE_URL = "https://your-streamlit-app-url"  # replace with your deployed app URL

survey_query = None
if hasattr(st, "experimental_get_query_params"):
    try:
        survey_query = st.experimental_get_query_params().get("survey", [None])[0]
    except Exception:
        survey_query = None
if survey_query:
    st.set_page_config(page_title="OMNI-FLOW Survey", layout="wide")
    st.title("📝 Customer Survey")
    cust = next((c for c in st.session_state.queue if c.get('id') == survey_query), None)
    if not cust:
        st.error("Survey link is invalid or the ticket has already been completed.")
    else:
        st.write(f"**Ticket:** {cust.get('id', 'UNKNOWN')}  ")
        st.write(f"**Item:** {cust.get('item', 'UNKNOWN')}  ")
        with st.form("survey_link_form"):
            score = st.select_slider("Rating", ["Poor", "Neutral", "Good", "Excellent"])
            root = st.selectbox("Failure Point", ["Wait Time", "Staff Attitude", "Quality", "Process"]) if score != "Excellent" else None
            if st.form_submit_button("SUBMIT SURVEY"):
                log = load_data(FILES["survey"], [])
                log.append({
                    "id": cust.get('id', 'UNKNOWN'),
                    "item": cust.get('item', 'UNKNOWN'),
                    "score": score,
                    "root": root
                })
                save_data(FILES["survey"], log)
                st.session_state.queue = [q for q in st.session_state.queue if q.get('id') != survey_query]
                save_data(FILES["queue"], st.session_state.queue)
                st.success("Thank you for your feedback!")
                st.experimental_set_query_params()
                st.stop()
    st.stop()

st.set_page_config(page_title="OMNI-FLOW V7.1", layout="wide")
st.title("🛡️ OMNI-FLOW: OPERATIONS COMMAND")

t1, t2, t3 = st.tabs(["➕ ENTRY", "⚙️ STAFF DASH", "📊 ANALYTICS"])

with t1:
    with st.form("entry_form", clear_on_submit=True):
        phone = st.text_input("CUSTOMER PHONE")
        item = st.text_input("ITEM NAME (e.g., Garlic Powder)")
        if st.form_submit_button("JOIN QUEUE"):
            # validate required fields
            if not phone or not phone.strip() or not item or not item.strip():
                st.error("Both phone and item are required to join the queue.")
            else:
                cid = str(uuid.uuid4())[:6]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                phone_norm = re.sub(r'\s+', '', phone)
                st.session_state.queue.append({
                    "id": cid, "phone": phone_norm, "item": item.strip(),
                    "status": "WAITING", "joined": timestamp
                })
                save_data(FILES["queue"], st.session_state.queue)
                # store last ticket and show a prominent confirmation
                st.session_state.last_ticket = cid
                survey_link = f"{SURVEY_BASE_URL}/?survey={cid}"
                notif_msg = (
                    f"Ticket {cid} issued at {timestamp}. "
                    f"When the order is served, the WhatsApp notification will be sent with this message:\n"
                    f"Your order of {item.strip()} (ID: {cid}) is ready! Served at: <served_time>. "
                    f"Please provide feedback: {survey_link}"
                )
                st.session_state.last_entry_notice = notif_msg
                st.success(f"Ticket {cid} issued at {timestamp}")
                st.balloons()

    # show the last issued ticket prominently for the user
    if st.session_state.last_ticket:
        st.info(f"Your Ticket ID: {st.session_state.last_ticket}")
    if st.session_state.last_entry_notice:
        st.warning(st.session_state.last_entry_notice)
with t2:
    for i, cust in enumerate(st.session_state.queue):
        col1, col2 = st.columns([3, 2])
        action_col, delete_col = col2.columns([3, 1])
        cust_id = cust.get('id', 'UNKNOWN')
        cust_item = cust.get('item', 'UNKNOWN')
        cust_phone = cust.get('phone', 'N/A')
        col1.write(f"**ID:** {cust_id} | **ITEM:** {cust_item} | **PH:** {cust_phone}")
        
        if cust['status'] == "WAITING":
            if action_col.button("SERVE", key=f"s_{i}"):
                cust['status'] = "SERVING"
                cust['served_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_data(FILES["queue"], st.session_state.queue); st.rerun()
        
        elif cust['status'] == "SERVING":
            cust_phone = cust.get('phone', '')
            served_at = cust.get('served_at', 'unknown time')
            if cust_phone:
                phone_fmt = re.sub(r"\D", "", cust_phone)
                survey_link = f"{SURVEY_BASE_URL}/?survey={cust_id}"
                msg = (
                    f"Your order of {cust_item} (ID: {cust_id}) is ready! Served at: {served_at}. "
                    f"Please provide feedback: {survey_link}"
                )
                wa_link = f"https://wa.me/{phone_fmt}?text={quote_plus(msg)}"
                action_col.markdown(
                    f'<a href="{wa_link}" target="_blank" style="text-decoration:none;">'
                    f'<button style="background-color:#25D366; color:white; border:none; padding:8px; border-radius:5px;">'
                    f'💬 MSG READY: {served_at}</button></a>',
                    unsafe_allow_html=True)
            else:
                action_col.info("No phone number available for WhatsApp notification.")
            
            if action_col.button("FINISH", key=f"f_{i}"):
                cust['status'] = "SURVEY"
                save_data(FILES["queue"], st.session_state.queue); st.rerun()
        
        elif cust['status'] == "SURVEY":
            with st.form(f"survey_{i}"):
                score = st.select_slider("Rating", ["Poor", "Neutral", "Good", "Excellent"])
                root = st.selectbox("Failure Point", ["Wait Time", "Staff Attitude", "Quality", "Process"]) if score != "Excellent" else None
                if st.form_submit_button("SUBMIT"):
                    log = load_data(FILES["survey"], [])
                    log.append({
                        "id": cust.get('id', 'UNKNOWN'),
                        "item": cust.get('item', 'UNKNOWN'),
                        "score": score,
                        "root": root
                    })
                    save_data(FILES["survey"], log)
                    st.session_state.queue.pop(i)
                    save_data(FILES["queue"], st.session_state.queue); st.rerun()
        
        # Edit / Delete controls
        if delete_col.button("EDIT", key=f"e_{i}"):
            st.session_state.edit_idx = i
            st.session_state.edit_phone = cust.get('phone', '')
            st.session_state.edit_item = cust.get('item', '')

        if st.session_state.edit_idx == i:
            new_phone = delete_col.text_input("Phone", value=st.session_state.get('edit_phone', ''), key=f"edit_phone_{i}")
            new_item = delete_col.text_input("Item", value=st.session_state.get('edit_item', ''), key=f"edit_item_{i}")
            if delete_col.button("SAVE", key=f"save_{i}"):
                st.session_state.queue[i]['phone'] = re.sub(r'\s+', '', new_phone)
                st.session_state.queue[i]['item'] = new_item.strip()
                save_data(FILES["queue"], st.session_state.queue)
                st.session_state.edit_idx = None
                st.experimental_rerun()
            if delete_col.button("CANCEL", key=f"cancel_{i}"):
                st.session_state.edit_idx = None

        if delete_col.button("DELETE", key=f"d_{i}"):
            st.session_state.delete_idx = i

        # password-protected delete
        try:
            admin_password = os.environ.get("OMNI_ADMIN_PWD") or (st.secrets.get("admin_password") if hasattr(st, 'secrets') else None)
        except Exception:
            admin_password = os.environ.get("OMNI_ADMIN_PWD")
        if not admin_password:
            admin_password = "admin"

        if st.session_state.delete_idx == i:
            password = delete_col.text_input("Admin Password", type="password", key=f"pwd_{i}")
            if delete_col.button("CONFIRM DELETE", key=f"confirm_d_{i}"):
                if password == admin_password:
                    st.session_state.queue.pop(i)
                    save_data(FILES["queue"], st.session_state.queue)
                    st.session_state.delete_idx = None
                    st.experimental_rerun()
                else:
                    st.error("Incorrect password. Delete canceled.")

