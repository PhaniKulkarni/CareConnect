import streamlit as st
from connection import SnowflakeConnection
from conversation_handler import ConversationHandler
from cortex_completion import CortexCompletion
import os
import time
from upload_prescription import upload_and_extract_prescription  # Import the prescription functionality
def initialize_session_state():
    """Initialize session state variables"""
    print("Initializing session state")
    if 'model_name' not in st.session_state:
        st.session_state.model_name = 'mixtral-8x7b'
    if 'category_value' not in st.session_state:
        st.session_state.category_value = 'ALL'
    if 'rag' not in st.session_state:
        st.session_state.rag = True
    if 'connection' not in st.session_state:
        st.session_state.connection = None
    if 'conversation_handler' not in st.session_state:
        st.session_state.conversation_handler = None
    if 'cortex_completion' not in st.session_state:
        st.session_state.cortex_completion = None

@st.cache_resource
def get_snowflake_connection():
    """Create and cache Snowflake connection"""
    connection = SnowflakeConnection()
    if not connection.connect():
        st.error("Failed to connect to Snowflake. Please check your credentials.")
        return None
    return connection

def config_sidebar():
    """Configure sidebar options"""
    st.sidebar.selectbox(
        'Select your model:',
        st.session_state.conversation_handler.available_models,
        key="model_name"
    )
    
    st.sidebar.selectbox(
        'Select what products you are looking for',
        st.session_state.conversation_handler.get_available_categories(),
        key="category_value"
    )
    
    st.session_state.rag = st.sidebar.checkbox('Use your own documents as context?', value=True)
    
    with st.sidebar.expander("Session State"):
        # Filter out connection objects from display
        display_state = {k: v for k, v in st.session_state.items() 
                        if k not in ['connection', 'conversation_handler', 'cortex_completion']}
        st.write(display_state)

def initialize_handlers():
    """Initialize handlers if not already in session state"""
    if st.session_state.connection is None:
        st.session_state.connection = get_snowflake_connection()
        if st.session_state.connection is None:
            return False
            
    if st.session_state.conversation_handler is None:
        session = st.session_state.connection.get_session()
        st.session_state.conversation_handler = ConversationHandler(session)
        
    if st.session_state.cortex_completion is None:
        session = st.session_state.connection.get_session()
        st.session_state.cortex_completion = CortexCompletion(
            session, 
            st.session_state.connection.get_root()
        )
    
    return True
def main():
    st.title(":speech_balloon: CareConnect")
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize handlers
    if not initialize_handlers():
        return
    
    # Configure sidebar
    config_sidebar()
    uploaded_prescription = st.file_uploader("Upload a Prescription (.doc, .docx, or .pdf)", type=["doc", "docx", "pdf"])
    prescription_text_chunks = []
    if uploaded_prescription:
        prescription_text_chunks = upload_and_extract_prescription(uploaded_prescription)
    # Display available documents
    st.write("This is the list of documents you already have and that will be used to answer your questions:")
    
    # Cache document list to avoid repeated queries
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_documents():
        return st.session_state.conversation_handler.get_available_documents()
    
    docs_df = get_documents()
    st.dataframe(docs_df)
    
    # Chat interface with memory management
    for msg in st.session_state.conversation_handler.get_history():
        with st.chat_message(msg.role):
            st.write(msg.content)
    
    # Chat input using chat_input instead of text_input for better UX
    question = st.chat_input(
        "Ask a question about the documents",
        key="chat_input"
    )
    
    if question:
        with st.chat_message("user"):
            st.write(question)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Get response
                prescription_text = "\n".join(prescription_text_chunks) if prescription_text_chunks else ""
                response_text, relative_paths = st.session_state.cortex_completion.complete(
                    question,
                    st.session_state.model_name,
                    st.session_state.rag,
                    prescription_text,
                    st.session_state.category_value
                )
                
                st.write(response_text)
                
                # Store the conversation
                st.session_state.conversation_handler.add_message("user", question)
                st.session_state.conversation_handler.add_message("assistant", response_text)
        
        # Display related documents
        if relative_paths:
            with st.sidebar.expander("Related Documents", expanded=True):
                for path in relative_paths:
                    url_link = st.session_state.cortex_completion.get_document_url(path)
                    if url_link:
                        display_url = f"Doc: [{path}]({url_link})"
                        st.sidebar.markdown(display_url)

if __name__ == "__main__":
    main()