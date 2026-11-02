import streamlit as st
import requests
import re

# 1. UI Configuration
st.set_page_config(page_title="NCERT RAG Explorer", page_icon="📚", layout="centered")
st.title("📚 NCERT Multimodal RAG")
st.markdown("Ask questions about Chapter 1: Power-sharing. The system retrieves text chunks and renders local diagrams dynamically.")

# 2. Backend API URLs
API_URL = "http://127.0.0.1:8000/query"
IMAGE_BASE_URL = "http://127.0.0.1:8000"

# 3. Chat Interface
question = st.text_input("Enter your question:", placeholder="E.g., What is majoritarianism in Sri Lanka?")

if st.button("Search") and question:
    with st.spinner("Searching textbook vectors..."):
        try:
            # Call your FastAPI backend
            response = requests.post(API_URL, json={"question": question})
            response.raise_for_status()
            data = response.json()
            
            # Display the main LLM Answer
            st.subheader("Synthesized Answer")
            st.info(data["answer"])
            
            # Display the Retrieved Metadata and Images
            st.subheader("Textbook Sources & Diagrams")
            for i, source in enumerate(data["sources"]):
                meta = source["metadata"]
                
                # Use the LLM-extracted metadata for the dropdown title
                expander_title = f"Source {i+1}: {meta.get('topic', 'Topic')} - {meta.get('subtopic', 'Subtopic')}"
                
                with st.expander(expander_title):
                    raw_text = source["text"]
                    
                    # Convert the relative markdown image paths to absolute FastAPI URLs
                    # Turns ![alt](/images (2).png) into ![alt](http://127.0.0.1:8000/images (2).png)
                    display_text = re.sub(
                        r'!\[(.*?)\]\((/images.*?)\)', 
                        rf'![\1]({IMAGE_BASE_URL}\2)', 
                        raw_text
                    )
                    
                    # Streamlit magically renders the text and the injected image
                    st.markdown(display_text)
                    
                    # Display the Hybrid Search Score and Chapter mapping
                    st.caption(f"**Relevance Score:** {source['score']:.4f} | **Chapter:** {meta.get('chapter_name', 'N/A')}")
                    
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to FastAPI. Is `uvicorn api:app --reload` running?")
        except Exception as e:
            st.error(f"An error occurred: {e}")