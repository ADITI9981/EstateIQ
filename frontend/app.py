
import os
import requests
import streamlit as st

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="EstateIQ | AI Real Estate Intelligence",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv(
    "ESTATEIQ_API_URL",
    "http://127.0.0.1:8000/chat"
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "focus_chat" not in st.session_state:
    st.session_state.focus_chat = False

# Create the first conversation if none exists
if st.session_state.active_conversation_id is None:
    chat_id = "chat_1"

    st.session_state.conversations[chat_id] = {
        "title": "New conversation",
        "messages": []
    }

    st.session_state.active_conversation_id = chat_id

# Access the currently selected conversation
active_chat = st.session_state.conversations[
    st.session_state.active_conversation_id
]

st.session_state.messages = active_chat["messages"]

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

/* Main application */
.stApp {
    background: #f5f7fb;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #101b32;
}

section[data-testid="stSidebar"] * {
    color: #f8fafc;
}

section[data-testid="stSidebar"] .stButton button {
    background: transparent;
    border: 1px solid transparent;
    color: #f8fafc;
    text-align: left !important;
    justify-content: flex-start !important;
    border-radius: 9px;
    min-height: 42px;
    font-size: 13px;
    transition: all 0.2s ease;
    padding-left: 16px !important;
}

/* Align the actual text inside sidebar buttons */
section[data-testid="stSidebar"] .stButton button p {
    width: 100%;
    text-align: left !important;
    margin: 0;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background: #263b5d;
    border-color: #405477;
}

/* Header */
.brand {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 3px;
    color: #b18a43;
    text-transform: uppercase;
}

.hero-title {
    font-size: clamp(32px, 5vw, 48px);
    font-weight: 750;
    color: #14213d;
    letter-spacing: -1.5px;
    margin-top: 8px;
    margin-bottom: 8px;
}

.hero-subtitle {
    font-size: 16px;
    color: #64748b;
    line-height: 1.7;
}

.section-label {
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

/* Welcome panel */
.welcome-panel {
    background: linear-gradient(135deg, #14213d, #263b5d);
    padding: 28px;
    border-radius: 18px;
    color: white;
    margin-top: 24px;
    margin-bottom: 25px;
}

.welcome-panel h3 {
    color: #ffffff;
    font-size: 23px;
    margin-bottom: 8px;
}

.welcome-panel p {
    color: #d5deeb;
    line-height: 1.7;
    margin-bottom: 0;
}

/* Information cards */
.info-card {
    background: white;
    border: 1px solid #e5eaf2;
    border-radius: 14px;
    padding: 19px;
    min-height: 125px;
}

.info-card h4 {
    color: #14213d;
    font-size: 16px;
    margin-bottom: 8px;
}

.info-card p {
    color: #64748b;
    font-size: 13px;
    line-height: 1.6;
}

/* Chat */
[data-testid="stChatMessage"] {
    background: white;
    border: 1px solid #e8edf4;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 12px;
}

[data-testid="stChatInput"] {
    background: white;
}

/* Buttons */
.stButton button {
    border-radius: 10px;
    font-weight: 600;
}

/* Sources */
.source-label {
    color: #b18a43;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-top: 15px;
}

/* Footer */
.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    padding-top: 30px;
}

/* Hide unnecessary Streamlit elements */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def render_sources(sources):
    if not sources:
        return

    st.markdown(
        '<div class="source-label">PROPERTY SOURCES</div>',
        unsafe_allow_html=True
    )

    for source in sources:
        if isinstance(source, str) and source.startswith("https://"):
            st.markdown(f"↗ [View original listing]({source})")


def render_message(message):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            render_sources(message.get("sources", []))


def ask_estateiq(question):
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    active_chat = st.session_state.conversations[
        st.session_state.active_conversation_id
    ]
    if active_chat["title"] == "New conversation":
        active_chat["title"] = (
            question[:40] + "..." if len(question) > 40 else question
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching property information and preparing your answer..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"question": question},
                    timeout=120
                )

                response.raise_for_status()
                result = response.json()

                answer = result.get("answer")

                if not answer:
                    raise ValueError("The backend returned an empty answer.")

                sources = result.get("sources", [])

                st.markdown(answer)
                render_sources(sources)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except requests.exceptions.ConnectionError:
                answer = (
                    "I cannot connect to the EstateIQ backend. "
                    "Please check whether the FastAPI server is running."
                )
                st.error(answer)

            except requests.exceptions.Timeout:
                answer = (
                    "The request took too long. Please try again."
                )
                st.error(answer)

            except requests.exceptions.HTTPError as error:
                answer = f"The backend returned an HTTP error: {error}"
                st.error(answer)

            except (ValueError, KeyError):
                answer = "The backend returned an unexpected response."
                st.error(answer)

            except requests.exceptions.RequestException as error:
                answer = f"An API request error occurred: {error}"
                st.error(answer)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    # Branding
    st.markdown(
        """
        <div style="padding: 15px 0 20px 0;">
            <div style="font-size: 34px;">🏡</div>
            <div style="font-size: 25px; font-weight: 750;">
                EstateIQ
            </div>
            <div style="font-size: 12px; color: #aab8cc;
                        letter-spacing: 1.5px;">
                AI REAL ESTATE INTELLIGENCE
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # New conversation
    if st.button(
        "＋ New conversation",
        key="new_conversation",
        use_container_width=True
    ):
        new_id = f"chat_{len(st.session_state.conversations) + 1}"

        st.session_state.conversations[new_id] = {
            "title": "New conversation",
            "messages": []
        }

        st.session_state.active_conversation_id = new_id
        st.session_state.messages = (
            st.session_state.conversations[new_id]["messages"]
        )
        st.session_state.pending_question = None
        st.rerun()

    st.divider()

    # Chat history
    st.markdown("### 🕘 Chat History")

    visible_chats = [
        (chat_id, chat)
        for chat_id, chat in reversed(
            list(st.session_state.conversations.items())
        )
        if chat["messages"]
    ]

    if not visible_chats:
        st.caption("Your previous conversations will appear here.")

    for chat_id, chat in visible_chats:

        is_active = (
            chat_id == st.session_state.active_conversation_id
        )

        label = chat["title"]

        if len(label) > 30:
            label = label[:30] + "..."

        if st.button(
            ("● " if is_active else "  ") + label,
            key=f"history_{chat_id}",
            use_container_width=True
        ):
            st.session_state.active_conversation_id = chat_id
            st.session_state.messages = chat["messages"]
            st.session_state.pending_question = None
            st.rerun()

    st.divider()

    # Suggested questions
    st.markdown("### ✨ Suggested Questions")

    examples = [
        "Find me a 9-bedroom villa in Riyadh",
        "What is the rent for one payment?",
        "What is the rent for two payments?",
        "How many bedrooms and bathrooms does the villa have?",
        "Tell me about The Astera project",
        "What do you know about the Jeddah development?"
    ]

    for index, example in enumerate(examples):

        if st.button(
            example,
            key=f"example_{index}",
            use_container_width=True
        ):
            st.session_state.pending_question = example
            st.rerun()

    st.divider()

    # Data sources
    st.markdown("### 🔎 Data Sources")

    st.markdown("**DarGlobal**")
    st.caption("Real estate developments and project information.")

    st.markdown("**Wasalt**")
    st.caption("Property listings and rental information.")

    st.divider()

    # Disclaimer
    st.caption(
        "Prices and availability may change. "
        "Always verify details on the original source website."
    )

# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.markdown(
    '<div class="brand">REAL ESTATE INTELLIGENCE PLATFORM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero-title">Discover properties smarter.</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero-subtitle">
        Meet EstateIQ, your AI-powered real estate assistant.
        Explore property information, compare rental options,
        and discover real estate developments through natural language.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="welcome-panel">
        <h3>Welcome to EstateIQ 👋</h3>
        <p>
            What are you looking for today? Ask about property prices,
            locations, bedrooms, rental options, or real estate projects.
            I'll find relevant information from the available data.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# INFORMATION CARDS
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="info-card">
            <h4>🏘️ Property Discovery</h4>
            <p>Explore available property information,
            locations and property features.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Explore Properties", key="property_card"):
        st.session_state.pending_question = (
            "Show me the available properties and their details."
        )
        st.rerun()

with col2:
    st.markdown(
        """
        <div class="info-card">
            <h4>🤖 AI Assistant</h4>
            <p>Ask questions in natural language
            and receive context-aware answers.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Ask AI Assistant", key="assistant_card"):
        st.session_state.focus_chat = True
        st.rerun()

with col3:
    st.markdown(
        """
        <div class="info-card">
            <h4>🔗 Verified Sources</h4>
            <p>Access original listing sources
            to verify property information.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("View Sources", key="sources_card"):
        st.session_state.pending_question = (
            "Show me the sources for the available property information."
        )
        st.rerun()

# --------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------

for message in st.session_state.messages:
    render_message(message)


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

question = st.chat_input(
    "Ask EstateIQ about properties, prices or developments..."
)

if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

if question:
    ask_estateiq(question)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
    """
    <div class="footer">
        EstateIQ · AI-powered Real Estate Intelligence
        <br>
        Property information should always be verified with its original source.
    </div>
    """,
    unsafe_allow_html=True
)
