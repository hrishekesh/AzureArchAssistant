import streamlit as st

from review_pipeline import build_metadata, extract_text, review_document


st.set_page_config(page_title="Azure Architecture Review", layout="wide")

st.title("Architecture Review Pipeline")
st.write(
    "Upload architecture documents to generate critical review comments, improvement "
    "suggestions aligned with Azure best practices, and a structured report."
)

uploaded_files = st.file_uploader(
    "Upload architecture documents",
    type=["txt", "md", "pdf", "docx"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Upload one or more documents to generate a review report.")
    st.stop()

for uploaded_file in uploaded_files:
    file_bytes = uploaded_file.getvalue()
    text = extract_text(uploaded_file.name, file_bytes)

    if not text.strip():
        st.warning(
            f"No readable text extracted from {uploaded_file.name}. "
            "Ensure the document is text-based or install PDF/DOCX dependencies."
        )
        continue

    metadata = build_metadata(uploaded_file.name, text)
    report = review_document(text, metadata)

    st.header(f"Report: {metadata.name}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Words", metadata.word_count)
    col2.metric("Characters", metadata.character_count)
    col3.metric("File type", metadata.file_type.upper())

    st.subheader("Summary")
    st.write(report["summary"])

    st.subheader("Critical Review Comments")
    if report["critical_comments"]:
        for finding in report["critical_comments"]:
            with st.expander(f"{finding.title} ({finding.severity.title()})", expanded=True):
                st.markdown(f"**Observation:** {finding.observation}")
                st.markdown(f"**Recommendation:** {finding.recommendation}")
                st.markdown(f"**Azure alignment:** {finding.azure_alignment}")
    else:
        st.success("No critical gaps detected based on keyword analysis.")

    st.subheader("Improvement Suggestions")
    for suggestion in report["improvement_suggestions"]:
        st.markdown(f"- {suggestion}")

    st.subheader("Best Practice Alignment")
    for item in report["best_practice_alignment"]:
        st.markdown(f"- {item}")

    st.subheader("Detailed Findings")
    for finding in report["findings"]:
        with st.expander(f"{finding.title} ({finding.severity.title()})"):
            st.markdown(f"**Observation:** {finding.observation}")
            st.markdown(f"**Recommendation:** {finding.recommendation}")
            st.markdown(f"**Azure alignment:** {finding.azure_alignment}")

    st.subheader("Next Steps")
    for step in report["next_steps"]:
        st.markdown(f"- {step}")
