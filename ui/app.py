import os
import re
import urllib.parse
import requests
import streamlit as st

st.set_page_config(
    page_title="NCERT Visual Knowledge Explorer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

backend_api_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
image_base_url = os.getenv("IMAGE_BASE_URL", "http://localhost:8000")
api_timeout_seconds = float(os.getenv("API_TIMEOUT", "300"))


def resolve_image_path(raw_path: str) -> str:
    if not raw_path:
        return ""
    decoded_value = urllib.parse.unquote(str(raw_path)).strip()
    extracted_filename = decoded_value.split("/")[-1].split("\\")[-1].strip()
    if not extracted_filename or extracted_filename == "local_path_placeholder":
        return ""

    candidate_filenames = [
        extracted_filename,
        f"{extracted_filename}.png",
        f"{extracted_filename}).png",
        f"{extracted_filename}.jpg"
    ]
    for candidate in candidate_filenames:
        disk_path = os.path.join("images", candidate)
        if os.path.exists(disk_path):
            return disk_path

    digit_finder = re.search(r'\((\d+)\)', decoded_value) or re.search(r'(\d+)', decoded_value)
    if digit_finder:
        found_digit = digit_finder.group(1)
        fallback_filename = f"images ({found_digit}).png"
        disk_path = os.path.join("images", fallback_filename)
        if os.path.exists(disk_path):
            return disk_path

    normalized_name = extracted_filename
    if normalized_name.count("(") > normalized_name.count(")"):
        normalized_name = f"{normalized_name})"
    if not any(normalized_name.endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
        normalized_name = f"{normalized_name}.png"

    encoded_name = urllib.parse.quote(normalized_name)
    return f"{image_base_url}/images/{encoded_name}"


st.markdown("""
<style>
    .main {
        background-color: #0b1120;
        color: #f1f5f9;
    }
    .header-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background-color: #0284c7;
        color: white;
        margin-right: 8px;
    }
    .badge-secondary {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        background-color: #334155;
        color: #94a3b8;
    }
    .insight-card {
        background: #1e293b;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 20px;
        margin-top: 16px;
        margin-bottom: 20px;
    }
    .diagram-frame {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 16px;
    }
    .diagram-caption {
        font-size: 13px;
        color: #cbd5e1;
        margin-top: 8px;
        font-style: italic;
    }
    .score-chip {
        background: #064e3b;
        color: #6ee7b7;
        font-size: 12px;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

if "active_question" not in st.session_state:
    st.session_state["active_question"] = "What is the ethnic composition of Belgium?"

if "cached_question" not in st.session_state:
    st.session_state["cached_question"] = None

if "cached_data" not in st.session_state:
    st.session_state["cached_data"] = None

if "run_search" not in st.session_state:
    st.session_state["run_search"] = False

with st.sidebar:
    st.markdown("### 🏛️ NCERT Visual Terminal")
    st.markdown("**Subject:** Democratic Politics - II")
    st.markdown("**Class:** Grade X")
    st.markdown("**Active Chapter:** Chapter 1: Power-sharing")
    st.divider()
    
    st.markdown("#### System Endpoints")
    st.text_input("Backend API", value=backend_api_url, key="api_url_input", disabled=True)
    st.text_input("Asset Server", value=image_base_url, key="asset_url_input", disabled=True)
    
    st.divider()
    st.markdown("#### Quick Explorations")
    exploration_queries = [
        "What is the ethnic composition of Belgium?",
        "What majoritarian measures were taken in Sri Lanka?",
        "Explain the accommodation model in Belgium.",
        "Why is power sharing desirable?",
        "What are the different forms of power sharing?"
    ]
    for preset_question in exploration_queries:
        if st.button(preset_question, key=f"btn_{preset_question}", use_container_width=True):
            st.session_state["active_question"] = preset_question
            st.session_state["run_search"] = True
            st.rerun()

st.markdown("""
<div class="header-box">
    <span class="badge-pill">Textbook Research Station</span>
    <span class="badge-secondary">Hybrid Semantic Search</span>
    <h1 style="color: #ffffff; margin-top: 10px; margin-bottom: 4px; font-size: 28px;">
        NCERT Democratic Politics: Power-Sharing Explorer
    </h1>
    <p style="color: #94a3b8; font-size: 15px; margin: 0;">
        Explore textbook excerpts, synthesize political concepts, and inspect historical maps and diagrams from Chapter 1.
    </p>
</div>
""", unsafe_allow_html=True)

search_col1, search_col2 = st.columns([5, 1])

with search_col1:
    user_input_query = st.text_input(
        "Enter research question:",
        value=st.session_state["active_question"],
        placeholder="Ask anything about Chapter 1 (e.g. How does power sharing prevent social conflict?)"
    )

with search_col2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    submit_search = st.button("Explore", use_container_width=True, type="primary")

active_search_query = user_input_query.strip()

if submit_search and active_search_query:
    st.session_state["active_question"] = active_search_query
    st.session_state["run_search"] = True

should_fetch = st.session_state.get("run_search", False) or (
    st.session_state.get("cached_data") is None and bool(active_search_query)
)

if should_fetch and active_search_query:
    st.session_state["run_search"] = False
    endpoint_target = f"{backend_api_url}/query"
    try:
        with st.spinner("Retrieving textbook passages and diagrams..."):
            query_payload = {"question": active_search_query}
            network_response = requests.post(
                endpoint_target,
                json=query_payload,
                timeout=api_timeout_seconds
            )
            network_response.raise_for_status()
            st.session_state["cached_data"] = network_response.json()
            st.session_state["cached_question"] = active_search_query
    except requests.exceptions.Timeout:
        st.error("The request timed out. Local Ollama is busy generating or taking longer than expected. Please try again.")
    except requests.exceptions.ConnectionError:
        st.error(f"Unable to connect to the backend API at {backend_api_url}. Please ensure FastAPI is running.")
    except Exception as runtime_error:
        st.error(f"Error fetching textbook data: {runtime_error}")

response_data = st.session_state.get("cached_data")

if response_data:
    analysis_column, visual_column = st.columns([3, 2], gap="large")

    with analysis_column:
        st.markdown("### 📖 Knowledge Synthesis")
        st.markdown(f"""
        <div class="insight-card">
            {response_data.get('answer', 'No answer synthesized.')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📑 Primary Textbook Sources")
        source_items = response_data.get("sources", [])
        if not source_items:
            st.info("No direct textbook passages retrieved.")
        
        for index_counter, source in enumerate(source_items):
            metadata_map = source.get("metadata", {})
            topic_title = metadata_map.get("topic", "General Section")
            subtopic_title = metadata_map.get("subtopic", "Concept")
            relevance_score = source.get("score")
            
            score_display = f"{relevance_score:.4f}" if relevance_score is not None else "Match"

            accordion_label = f"Excerpt {index_counter + 1}: {topic_title} - {subtopic_title}"
            with st.expander(accordion_label, expanded=(index_counter == 0)):
                passage_text = source.get("text", "")

                def rewrite_image_markdown_match(match_object):
                    caption_text = match_object.group(1)
                    image_target = match_object.group(2)
                    located_image = resolve_image_path(image_target)
                    if located_image:
                        file_basename = os.path.basename(located_image)
                        encoded_filename = urllib.parse.quote(file_basename)
                        return f"![{caption_text}]({image_base_url}/images/{encoded_filename})"
                    return f"![{caption_text}]({image_target})"

                rewritten_passage = re.sub(
                    r'!\[(.*?)\]\((.+?\.(?:png|jpg|jpeg|webp|svg|gif|bmp)|[^\s\)]+)\)',
                    rewrite_image_markdown_match,
                    passage_text
                )
                
                st.markdown(rewritten_passage)
                
                st.markdown(f"""
                <div style="display: flex; gap: 10px; align-items: center; margin-top: 10px;">
                    <span class="score-chip">Relevance: {score_display}</span>
                    <span style="color: #94a3b8; font-size: 13px;">Chapter: {metadata_map.get('chapter_name', 'Power-sharing')}</span>
                </div>
                """, unsafe_allow_html=True)

    with visual_column:
        st.markdown("### 🗺️ Visual Evidence & Diagrams")
        
        found_diagrams = []
        for source in source_items:
            metadata_map = source.get("metadata", {})
            raw_image_target = source.get("image_url") or metadata_map.get("image_url")
            
            if raw_image_target:
                resolved_target = resolve_image_path(raw_image_target)
                if resolved_target:
                    found_diagrams.append({
                        "source": resolved_target,
                        "caption": source.get("image_caption") or metadata_map.get("image_caption") or "Textbook Figure",
                        "topic": metadata_map.get("topic", "Illustration")
                    })

        for direct_image_url in response_data.get("images", []):
            resolved_direct = resolve_image_path(direct_image_url)
            if resolved_direct and not any(d["source"] == resolved_direct for d in found_diagrams):
                found_diagrams.append({
                    "source": resolved_direct,
                    "caption": "Textbook Diagram Reference",
                    "topic": "Visual Document"
                })

        if found_diagrams:
            for diagram in found_diagrams:
                st.markdown(f"""
                <div class="diagram-frame">
                    <div style="font-weight: 600; color: #38bdf8; font-size: 14px; margin-bottom: 6px;">
                        {diagram['topic']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.image(diagram["source"], caption=diagram["caption"], use_container_width=True)
        else:
            st.info("No diagrams specifically referenced for this section. Consult the Chapter Overview for full visual gallery.")
            st.markdown("""
            <div class="diagram-frame">
                <p style="color: #94a3b8; font-size: 13px; margin: 0;">
                    Available diagrams in this chapter include:
                    <br>• Map of Belgian Linguistic Communities
                    <br>• Ethnic Distribution Map of Sri Lanka
                    <br>• European Parliament Brussels Building
                    <br>• German Coalition Car Cartoon
                </p>
            </div>
            """, unsafe_allow_html=True)
