# pyrefly: ignore [missing-import]
import streamlit as st
from pathlib import Path
from knowledge_manager import process_transcript, get_kb_statistics

# Page config
st.set_page_config(page_title="Meeting Knowledge Assistant", layout="wide")

# Resolve database path
db_path = Path(__file__).parent / "database" / "terms.db"

# Sidebar: Admin Dashboard
st.sidebar.title("Knowledge Base Statistics")
stats = get_kb_statistics(db_path)
st.sidebar.metric("Total Terms", stats.get("total_terms", 0))
st.sidebar.metric("AI Generated Terms", stats.get("ai_generated", 0))
st.sidebar.metric("Manual Terms", stats.get("manual_terms", 0))
st.sidebar.metric("Flagged Terms", stats.get("flagged_terms", 0))
st.sidebar.metric("Deleted Terms", stats.get("deleted_terms", 0))

health_pct = stats.get("health_percent", 100)
st.sidebar.metric("Knowledge Base Health", f"{health_pct}%")

if stats.get("total_terms", 0) > 0 and (stats.get("flagged_terms", 0) / stats.get("total_terms", 1)) > 0.05:
    st.sidebar.warning("Warning: Flagged terms exceed 5%. Please run cleanup_database.py.")

st.sidebar.markdown("### Top Categories")
for cat in stats.get("top_categories", []):
    st.sidebar.markdown(f"- **{cat['category']}**: {cat['count']}")

# UI Title and Instructions
st.title("Meeting Knowledge Assistant")
st.markdown("Paste meeting notes, transcripts, or technical discussions to get instant explanations of technical terms.")

# Input Area
text_input = st.text_area(
    "Transcript", 
    height=200, 
    placeholder="The LangGraph workflow uses OpenTelemetry and DSPy.",
    label_visibility="collapsed"
)

# Initialize session state to manage interactions smoothly
if 'explained' not in st.session_state:
    st.session_state['explained'] = False

# Button Action
if st.button("Explain Terms"):
    if text_input.strip():
        with st.spinner('Analyzing transcript and generating AI definitions...'):
            # Call the new hybrid knowledge manager
            results = process_transcript(text_input, db_path)
            
            st.session_state['results'] = results
            st.session_state['db_path'] = db_path
            st.session_state['explained'] = True
    else:
        st.warning("Please enter some text to explain.")
        st.session_state['explained'] = False

# Render the Results below the input
if st.session_state['explained']:
    results = st.session_state['results']
    known = results.get("known_terms", [])
    newly_learned = results.get("newly_learned_terms", [])
    unknown = results.get("unknown_terms", [])
    
    # Display in three columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Known Technical Terms")
        if not known:
            st.info("No known terms detected.")
        else:
            for res in known:
                title = res['term']
                if res['term'].lower() != res.get('matched_text', res['term']).lower():
                    title += f" *(Matched as: {res.get('matched_text', res['term'])})*"
                
                with st.expander(title):
                    st.markdown(f"**Definition:** {res.get('definition', '')}")
                    st.markdown(f"**Category:** {res.get('category', 'Unknown')}")
                    st.markdown(f"**Term Type:** {res.get('term_type', 'Other')}")
                    if 'source' in res:
                        st.markdown(f"**Source:** {res['source']} | **Confidence:** {res.get('confidence', 'High')}")
                    
    with col2:
        st.subheader("Newly Learned Terms")
        if not newly_learned:
            st.info("No new terms learned.")
        else:
            for term_data in newly_learned:
                title = f"✓ {term_data['term']}" if term_data.get('saved') else f"⚠ {term_data['term']}"
                with st.expander(title):
                    if term_data.get('saved'):
                        st.success("Auto-Saved to Database")
                    else:
                        st.warning("Generated on the fly (Not Saved)")
                    
                    st.markdown(f"**Definition:** {term_data.get('definition', '')}")
                    st.markdown(f"**Category:** {term_data.get('category', 'Other')}")
                    st.markdown(f"**Term Type:** {term_data.get('term_type', 'Other')}")
                    st.markdown(f"**Source:** {term_data.get('source', 'AI Extraction')} | **Confidence:** {term_data.get('confidence', 'Medium')}")
                    
    with col3:
        st.subheader("Unknown Technical Terms")
        if not unknown:
            st.info("No unresolved unknown terms.")
        else:
            for unk in unknown:
                with st.expander(unk):
                    st.markdown("This term could not be defined by the AI.")
