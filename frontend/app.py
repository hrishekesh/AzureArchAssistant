import os

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Azure Architecture Assistant", layout="centered")

st.title("Azure Architecture Assistant")

st.subheader("Solution context")
context_text = st.text_area(
    "Describe the solution context",
    placeholder="E.g., data ingestion pipeline for IoT devices with real-time analytics...",
    height=180,
)

if st.button("Generate high-level architecture"):
    if not context_text.strip():
        st.warning("Please enter solution context before generating.")
    else:
        response = requests.post(
            f"{BACKEND_URL}/generate",
            json={"context": context_text},
            timeout=30,
        )
        response.raise_for_status()
        st.session_state["generation_result"] = response.json()

result = st.session_state.get("generation_result")
if result:
    st.subheader("Generated high-level solution")
    st.write(result["summary"])
    st.markdown("**Suggested components**")
    for component in result["components"]:
        st.markdown(f"- {component}")

st.divider()

st.subheader("Architecture document review")
uploaded_file = st.file_uploader("Upload an architecture document", type=["pdf", "docx", "txt"])

if st.button("Review uploaded document"):
    if uploaded_file is None:
        st.warning("Please upload a document for review.")
    else:
        files = {"document": (uploaded_file.name, uploaded_file.getvalue())}
        response = requests.post(
            f"{BACKEND_URL}/review",
            files=files,
            timeout=30,
        )
        response.raise_for_status()
        review = response.json()
        st.success(f"Review for {review['filename']}")
        st.write(review["notes"])
