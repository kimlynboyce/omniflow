import streamlit as st
import uuid, json, os
from datetime import datetime

# --- SYSTEM CONFIG ---
FILES = {"queue": "queue_data.json", "survey": "survey_log.json"}

def load_data(f, d): return json.load(open(f, 'r')) if os.path.exists(f) else d
def save_data(f, d): 
    with open(f, 'w') as file: json.dump(d, file, indent=4)

if 'queue' not in st.session_state: st.session_state.queue = load_data(FILES["queue"], [])

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
        col1.write(f"**ID:** {cust['id']} | **ITEM:** {cust['item']} | **PH:** {cust['phone']}")
        
        if cust['status'] == "WAITING":
            if col2.button("SERVE", key=f"s_{i}"):
                cust['status'] = "SERVING"
                cust['served_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_data(FILES["queue"], st.session_state.queue); st.rerun()
        
        elif cust['status'] == "SERVING":
            phone_fmt = cust['phone'].replace('+', '').replace(' ', '')
            msg = f"Your order of {cust['item']} (ID: {cust['id']}) is ready! Served at: {cust['served_at']}"
            wa_link = f"https://wa.me/{phone_fmt}?text={msg.replace(' ', '%20')}"
            
            col2.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;">'
                          f'<button style="background-color:#25D366; color:white; border:none; padding:8px; border-radius:5px;">'
                          f'💬 MSG READY: {cust["served_at"]}</button></a>', unsafe_allow_html=True)
            
            if col2.button("FINISH", key=f"f_{i}"):
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
