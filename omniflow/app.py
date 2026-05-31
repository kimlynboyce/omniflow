import streamlit as st
import uuid, json, os
from datetime import datetime

# --- SYSTEM CONFIG ---
FILES = {"queue": "queue_data.json", "survey": "survey_log.json"}

def load_data(f, d): return json.load(open(f, 'r')) if os.path.exists(f) else d
def save_data(f, d): 
    with open(f, 'w') as file: json.dump(d, file, indent=4)

if 'queue' not in st.session_state: st.session_state.queue = load_data(FILES["queue"], [])
if 'delete_idx' not in st.session_state: st.session_state.delete_idx = None

st.set_page_config(page_title="OMNI-FLOW V7.1", layout="wide")
st.title("🛡️ OMNI-FLOW: OPERATIONS COMMAND")

t1, t2, t3 = st.tabs(["➕ ENTRY", "⚙️ STAFF DASH", "📊 ANALYTICS"])

with t1:
    with st.form("entry_form", clear_on_submit=True):
        phone = st.text_input("CUSTOMER PHONE")
        item = st.text_input("ITEM NAME (e.g., Garlic Powder)")
        if st.form_submit_button("JOIN QUEUE"):
            cid = str(uuid.uuid4())[:6]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.queue.append({
                "id": cid, "phone": phone, "item": item, 
                "status": "WAITING", "joined": timestamp
            })
            save_data(FILES["queue"], st.session_state.queue)
            st.success(f"Ticket {cid} issued at {timestamp}")

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
                phone_fmt = cust_phone.replace('+', '').replace(' ', '')
                msg = f"Your order of {cust_item} (ID: {cust_id}) is ready! Served at: {served_at}"
                wa_link = f"https://wa.me/{phone_fmt}?text={msg.replace(' ', '%20')}"
                action_col.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;">'
                              f'<button style="background-color:#25D366; color:white; border:none; padding:8px; border-radius:5px;">'
                              f'💬 MSG READY: {served_at}</button></a>', unsafe_allow_html=True)
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
                    log.append({"id": cust['id'], "item": cust['item'], "score": score, "root": root})
                    save_data(FILES["survey"], log)
                    st.session_state.queue.pop(i)
                    save_data(FILES["queue"], st.session_state.queue); st.rerun()
        
        if delete_col.button("DELETE", key=f"d_{i}"):
            st.session_state.delete_idx = i

        if st.session_state.delete_idx == i:
            password = delete_col.text_input("Admin Password", type="password", key=f"pwd_{i}")
            if delete_col.button("CONFIRM DELETE", key=f"confirm_d_{i}"):
                if password == "admin":
                    st.session_state.queue.pop(i)
                    save_data(FILES["queue"], st.session_state.queue)
                    st.session_state.delete_idx = None
                    st.experimental_rerun()
                else:
                    st.error("Incorrect password. Delete canceled.")

