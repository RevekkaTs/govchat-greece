import requests
import streamlit as st

API_URL = "http://localhost:8000"

DOMAIN_LABELS = {
    "road_safety": "🚗 Τροχαία ατυχήματα",
    "fires": "🔥 Δασικές πυρκαγιές",
    "energy": "⚡ Ενέργεια",
}

st.set_page_config(page_title="GovChat Greece", page_icon="🏛️", layout="centered")

st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
* { font-family: 'Roboto', sans-serif !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stSidebar"] p { font-size: 0.82rem; }
#MainMenu { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
</style>
""",
    unsafe_allow_html=True,
)


def api_login(username: str, password: str):
    try:
        return requests.post(
            f"{API_URL}/auth/login", data={"username": username, "password": password}
        )
    except Exception:
        return None


def api_create_session(token: str, title: str = "Νέα συνομιλία"):
    try:
        r = requests.post(
            f"{API_URL}/chat/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": title},
        )
        if r.status_code == 201:
            return r.json()
        return None
    except Exception:
        return None


def api_get_sessions(token: str):
    try:
        r = requests.get(
            f"{API_URL}/chat/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


def api_get_messages(token: str, session_id: int):
    try:
        r = requests.get(
            f"{API_URL}/chat/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


def api_send_message(token: str, session_id: int, content: str):
    try:
        r = requests.post(
            f"{API_URL}/chat/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": content},
            timeout=60,
        )
        return r.json()
    except requests.exceptions.ConnectionError:
        return {
            "error": "Δεν είναι δυνατή η σύνδεση με τον server. Βεβαιωθείτε ότι το FastAPI τρέχει."
        }
    except Exception as e:
        return {"error": str(e)}


# -- Session state defaults
if "token" not in st.session_state:
    st.session_state.token = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []


# -- Auth screen
if not st.session_state.token:
    st.title("🏛️ GovChat Greece")
    st.caption("AI chatbot για ελληνικά ανοιχτά δεδομένα του δημοσίου (data.gov.gr)")
    st.divider()

    with st.form("login_form"):
        username = st.text_input("Όνομα χρήστη")
        password = st.text_input("Κωδικός", type="password")
        if st.form_submit_button("Σύνδεση", use_container_width=True):
            r = api_login(username, password)
            if r is None:
                st.error("Δεν είναι δυνατή η σύνδεση με τον server.")
            elif r.status_code == 200:
                st.session_state.token = r.json()["access_token"]
                result = api_create_session(st.session_state.token)
                if result:
                    st.session_state.session_id = result["id"]
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.session_state.token = None
                    st.error("Αδυναμία δημιουργίας συνομιλίας.")
            else:
                st.error("Λάθος όνομα χρήστη ή κωδικός.")

    st.stop()


# -- Chat screen
with st.sidebar:
    st.title("🏛️ GovChat Greece")
    st.caption("Συζητήστε με τα ανοιχτά δεδομένα του δημοσίου")
    st.divider()

    if st.button("＋ Νέα συνομιλία", use_container_width=True):
        new = api_create_session(st.session_state.token)
        if new:
            st.session_state.session_id = new["id"]
            st.session_state.messages = []
            st.rerun()
        else:
            st.error("Αδυναμία δημιουργίας συνομιλίας.")

    sessions = api_get_sessions(st.session_state.token)
    visible = [
        s
        for s in reversed(sessions)
        if s["title"] != "Νέα συνομιλία" or s["id"] == st.session_state.session_id
    ][:10]
    if visible:
        st.markdown("**Συνομιλίες**")
        for s in visible:
            label = s["title"]
            if st.button(label, key=f"session_{s['id']}", use_container_width=True):
                st.session_state.session_id = s["id"]
                raw = api_get_messages(st.session_state.token, s["id"])
                st.session_state.messages = [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "domain": m.get("domain"),
                    }
                    for m in raw
                ]

    st.divider()
    st.markdown("**Θεματικές περιοχές**")
    st.markdown(
        '<p style="white-space: nowrap;">🚗 Τροχαία ατυχήματα (2021–2025)</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="white-space: nowrap;">🔥 Δασικές πυρκαγιές (2021–2024)</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="white-space: nowrap;">⚡ Ενέργεια (ΑΔΜΗΕ)</p>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("**Ενδεικτικές ερωτήσεις**")
    st.markdown("_Πόσα θανατηφόρα τροχαία συνέβησαν το 2022;_")
    st.markdown("_Τι έκταση κάηκε το 2023;_")
    st.markdown("_Ποιοι είναι οι στόχοι ΑΠΕ στην Ελλάδα;_")
    st.divider()
    if st.button("Αποσύνδεση", use_container_width=True):
        st.session_state.token = None
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()


def show_user_message(content: str):
    _, col = st.columns([1, 3])
    with col:
        with st.chat_message("user", avatar="🧑"):
            st.markdown(content)


def show_assistant_message(content: str, domain: str | None):
    col, _ = st.columns([3, 1])
    with col:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(content)
            if domain:
                st.caption(f"Πηγή δεδομένων: {DOMAIN_LABELS.get(domain, domain)}")


# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        show_user_message(msg["content"])
    else:
        show_assistant_message(msg["content"], msg.get("domain"))

# Chat input
if prompt := st.chat_input("Κάντε μια ερώτηση..."):
    if st.session_state.session_id is None:
        result = api_create_session(st.session_state.token)
        if result:
            st.session_state.session_id = result["id"]
        else:
            st.error("Αδυναμία δημιουργίας συνομιλίας.")
            st.stop()
    show_user_message(prompt)

    col2, _ = st.columns([3, 1])
    with col2:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Αναζήτηση δεδομένων..."):
                result = api_send_message(
                    st.session_state.token, st.session_state.session_id, prompt
                )
                if "error" in result:
                    answer = f"⚠️ {result['error']}"
                    domain = None
                elif "detail" in result:
                    answer = f"⚠️ Server error: {result['detail']}"
                    domain = None
                else:
                    assistant = result.get("assistant_message", {})
                    answer = assistant.get("content", "⚠️ Unexpected response format.")
                    domain = assistant.get("domain")
            st.markdown(answer)
            if domain:
                st.caption(f"Πηγή δεδομένων: {DOMAIN_LABELS.get(domain, domain)}")

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "domain": domain}
    )
