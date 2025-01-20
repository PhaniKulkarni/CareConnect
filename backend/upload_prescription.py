import os
from langchain_community.document_loaders import PyMuPDFLoader # Import LangChain loader for .doc files
from langchain.text_splitter import RecursiveCharacterTextSplitter
import streamlit as st

def extract_text_from_doc(file_path: str) -> list:
    """Extract text from the uploaded document using LangChain."""
    try:
        # Load the document
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()
        
        # Combine all text from the document
        full_text = "\n".join([doc.page_content for doc in documents])
        
        # Split the text into chunks for better processing
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
        chunks = text_splitter.split_text(full_text)
        
        return chunks
    except Exception as e:
        st.error(f"Failed to extract text from the document: {e}")
        return []

def upload_and_extract_prescription(uploaded_file) -> list:
    """Handle prescription upload and extract text."""
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        file_path = f"temp_{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        
        # Extract text using LangChain
        with st.spinner("Extracting text from the prescription..."):
            extracted_chunks = extract_text_from_doc(file_path)
            if extracted_chunks:
                st.success(f"Text extracted successfully from {uploaded_file.name}.")
            else:
                st.error(f"Failed to extract text from {uploaded_file.name}.")
        
        # Remove the temporary file
        os.remove(file_path)
        return extracted_chunks
    return []
