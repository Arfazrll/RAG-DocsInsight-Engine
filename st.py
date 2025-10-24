import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st
from langchain_community.document_loaders import (
    PDFPlumberLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    CSVLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import pandas as pd

st.set_page_config(
    page_title="Enterprise RAG System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_enhanced_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        .main {
            background: #000000;
            padding: 0;
        }
        
        [data-testid="stSidebar"] {
            background: #0a0a0a;
            border-right: 1px solid #1a1a1a;
        }
        
        .hero-section {
            background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%);
            padding: 3rem 2rem;
            text-align: center;
            border-bottom: 1px solid #2a2a2a;
            margin-bottom: 2rem;
        }
        
        .hero-title {
            font-size: 3rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.5rem;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            color: #888888;
            margin-bottom: 1.5rem;
        }
        
        .ai-badge {
            display: inline-block;
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            padding: 0.4rem 1.2rem;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            font-size: 0.85rem;
            margin: 0.3rem;
        }
        
        .content-section {
            background: #000000;
            padding: 2rem;
        }
        
        .stat-card {
            background: #0f0f0f;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #2a2a2a;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            background: #1a1a1a;
            border-color: #4F46E5;
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(79, 70, 229, 0.2);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-label {
            color: #888888;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        .section-header {
            font-size: 1.8rem;
            font-weight: 600;
            color: #ffffff;
            margin: 2.5rem 0 1.5rem 0;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #4F46E5;
        }
        
        .chat-message {
            background: #0f0f0f;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #2a2a2a;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .chat-message:hover {
            background: #1a1a1a;
            border-color: #4F46E5;
        }
        
        .message-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.8rem;
        }
        
        .user-badge {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            color: white;
            font-weight: 600;
            font-size: 0.75rem;
            display: inline-block;
            margin-right: 0.5rem;
        }
        
        .assistant-badge {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            color: white;
            font-weight: 600;
            font-size: 0.75rem;
            display: inline-block;
            margin-right: 0.5rem;
        }
        
        .timestamp-badge {
            background: #7C3AED;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }
        
        .confidence-badge {
            background: #10B981;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            display: inline-block;
            margin: 0.5rem 0.5rem 0.5rem 0;
        }
        
        .source-badge {
            background: #7C3AED;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            display: inline-block;
            margin: 0.5rem 0.5rem 0.5rem 0;
        }
        
        .document-card {
            background: #0f0f0f;
            padding: 1.2rem;
            border-radius: 10px;
            border: 1px solid #2a2a2a;
            margin: 0.8rem 0;
            transition: all 0.3s ease;
        }
        
        .document-card:hover {
            background: #1a1a1a;
            border-color: #4F46E5;
            transform: translateX(5px);
        }
        
        .doc-title {
            font-size: 1rem;
            font-weight: 600;
            color: #4F46E5;
            margin-bottom: 0.5rem;
        }
        
        .doc-meta {
            color: #888888;
            font-size: 0.85rem;
            margin: 0.3rem 0;
        }
        
        .info-box {
            background: #0f0f0f;
            padding: 1.2rem;
            border-radius: 8px;
            border-left: 3px solid #4F46E5;
            color: #cccccc;
            margin: 1rem 0;
        }
        
        .success-box {
            background: #0f0f0f;
            padding: 1rem;
            border-radius: 8px;
            border-left: 3px solid #10B981;
            color: #10B981;
            margin: 1rem 0;
        }
        
        .warning-box {
            background: #0f0f0f;
            padding: 1rem;
            border-radius: 8px;
            border-left: 3px solid #F59E0B;
            color: #F59E0B;
            margin: 1rem 0;
        }
        
        .stButton>button {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(79, 70, 229, 0.4);
        }
        
        .stTextArea textarea, .stTextInput input {
            background: #0a0a0a !important;
            border: 1px solid #2a2a2a !important;
            color: white !important;
            border-radius: 8px !important;
        }
        
        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #4F46E5 !important;
        }
        
        .stSelectbox div[data-baseweb="select"] > div {
            background: #0a0a0a !important;
            border: 1px solid #2a2a2a !important;
            border-radius: 8px !important;
        }
        
        .stRadio > div {
            background: #0a0a0a;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #2a2a2a;
        }
        
        .stCheckbox {
            background: #0a0a0a;
            padding: 0.5rem;
            border-radius: 6px;
        }
        
        [data-testid="stExpander"] {
            background: #0a0a0a;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
        }
        
        div[data-testid="stExpander"] div[role="button"] p {
            color: #4F46E5 !important;
            font-weight: 600;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #0a0a0a;
            border-radius: 10px;
            padding: 0.5rem;
            border: 1px solid #2a2a2a;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 8px;
            color: #888888;
            font-weight: 500;
            padding: 0.8rem 1.5rem;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white !important;
        }
        
        .stDataFrame {
            background-color: #0a0a0a;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
        }
        
        label, .stMarkdown p, .stMarkdown li {
            color: #cccccc !important;
        }
        
        h1, h2, h3, h4 {
            color: #ffffff !important;
        }
        
        .footer {
            text-align: center;
            padding: 2rem;
            color: #555555;
            border-top: 1px solid #1a1a1a;
            margin-top: 3rem;
        }
        
        .upload-section {
            background: #0f0f0f;
            padding: 1.5rem;
            border-radius: 10px;
            border: 2px dashed #2a2a2a;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .upload-section:hover {
            border-color: #4F46E5;
            background: #1a1a1a;
        }
        
        [data-testid="stFileUploader"] {
            background: transparent;
        }
        
        .stChatInput > div {
            background: #0a0a0a !important;
            border: 1px solid #2a2a2a !important;
            border-radius: 10px !important;
        }
        
        .stChatInput input {
            color: white !important;
        }
        
        .sidebar-section {
            background: #0f0f0f;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #2a2a2a;
            margin: 1rem 0;
        }
        
        .sidebar-title {
            color: #4F46E5;
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)


class DocumentProcessor:
    
    SUPPORTED_FORMATS = {
        'pdf': PDFPlumberLoader,
        'docx': Docx2txtLoader,
        'doc': Docx2txtLoader,
        'xlsx': UnstructuredExcelLoader,
        'xls': UnstructuredExcelLoader,
        'csv': CSVLoader,
        'txt': TextLoader
    }
    
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = storage_path
        self.docs_path = os.path.join(storage_path, "documents")
        self.db_path = os.path.join(storage_path, "vectordb")
        self.metadata_path = os.path.join(storage_path, "metadata")
        
        for path in [self.docs_path, self.db_path, self.metadata_path]:
            os.makedirs(path, exist_ok=True)
    
    def generate_file_hash(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()
    
    def save_file(self, uploaded_file) -> Dict:
        file_bytes = uploaded_file.getvalue()
        file_hash = self.generate_file_hash(file_bytes)
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        file_path = os.path.join(self.docs_path, f"{file_hash}.{file_ext}")
        
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
        
        metadata = {
            'filename': uploaded_file.name,
            'file_hash': file_hash,
            'file_type': file_ext,
            'file_size': len(file_bytes),
            'upload_date': datetime.now().isoformat(),
            'file_path': file_path
        }
        
        metadata_file = os.path.join(self.metadata_path, f"{file_hash}.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    def load_document(self, file_path: str, file_type: str) -> List[Document]:
        loader_class = self.SUPPORTED_FORMATS.get(file_type)
        
        if not loader_class:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        if file_type == 'csv':
            loader = loader_class(file_path, encoding='utf-8')
        else:
            loader = loader_class(file_path)
        
        return loader.load()
    
    def process_documents(self, documents: List[Document], metadata: Dict) -> List[Document]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )
        
        chunks = text_splitter.split_documents(documents)
        
        for chunk in chunks:
            chunk.metadata.update({
                'source_file': metadata['filename'],
                'file_hash': metadata['file_hash'],
                'file_type': metadata['file_type'],
                'upload_date': metadata['upload_date']
            })
        
        return chunks
    
    def get_all_metadata(self) -> List[Dict]:
        metadata_list = []
        
        for filename in os.listdir(self.metadata_path):
            if filename.endswith('.json'):
                with open(os.path.join(self.metadata_path, filename), 'r') as f:
                    metadata_list.append(json.load(f))
        
        return sorted(metadata_list, key=lambda x: x['upload_date'], reverse=True)
    
    def delete_document(self, file_hash: str):
        file_metadata = os.path.join(self.metadata_path, f"{file_hash}.json")
        
        if os.path.exists(file_metadata):
            with open(file_metadata, 'r') as f:
                metadata = json.load(f)
            
            if os.path.exists(metadata['file_path']):
                os.remove(metadata['file_path'])
            
            os.remove(file_metadata)
            
            return True
        return False


class VectorStoreManager:
    
    def __init__(self, db_path: str, embedding_model: str = "llama3:8b"):
        self.db_path = db_path
        self.embedding_function = OllamaEmbeddings(model=embedding_model)
        self.vector_store = None
        self.initialize_store()
    
    def initialize_store(self):
        try:
            self.vector_store = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embedding_function
            )
        except Exception:
            self.vector_store = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embedding_function
            )
    
    def add_documents(self, documents: List[Document]):
        if self.vector_store:
            self.vector_store.add_documents(documents)
        else:
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embedding_function,
                persist_directory=self.db_path
            )
    
    def search(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Document]:
        if not self.vector_store:
            return []
        
        if filter_dict:
            return self.vector_store.similarity_search(query, k=k, filter=filter_dict)
        else:
            return self.vector_store.similarity_search(query, k=k)
    
    def delete_by_source(self, file_hash: str):
        if self.vector_store:
            try:
                self.vector_store.delete(where={"file_hash": file_hash})
            except Exception:
                pass


class RAGQueryEngine:
    
    def __init__(self, model_name: str = "llama3:8b"):
        self.llm = OllamaLLM(model=model_name, temperature=0.7)
        self.prompt_template = ChatPromptTemplate.from_template("""
You are an enterprise-grade AI assistant specialized in document analysis and information retrieval.

Context from documents:
{context}

User query: {query}

Instructions:
1. Provide accurate, well-structured answers based on the context
2. Cite specific sources when making claims
3. If information is not in the context, clearly state that
4. Maintain professional tone suitable for business environments
5. Highlight key insights and actionable information

Answer:""")
    
    def generate_response(self, query: str, context_documents: List[Document]) -> Dict:
        if not context_documents:
            return {
                'answer': "No relevant documents found. Please upload documents or refine your query.",
                'sources': [],
                'confidence': 0.0
            }
        
        context_text = "\n\n".join([
            f"Source: {doc.metadata.get('source_file', 'Unknown')}\nContent: {doc.page_content}"
            for doc in context_documents
        ])
        
        chain = self.prompt_template | self.llm
        response = chain.invoke({
            'context': context_text,
            'query': query
        })
        
        sources = list(set([doc.metadata.get('source_file', 'Unknown') for doc in context_documents]))
        
        confidence = min(len(context_documents) / 5.0, 1.0)
        
        return {
            'answer': response,
            'sources': sources,
            'confidence': confidence,
            'num_sources': len(context_documents)
        }


def init_session_state():
    if 'processor' not in st.session_state:
        st.session_state.processor = DocumentProcessor()
    
    if 'vector_manager' not in st.session_state:
        st.session_state.vector_manager = VectorStoreManager(
            st.session_state.processor.db_path
        )
    
    if 'query_engine' not in st.session_state:
        st.session_state.query_engine = RAGQueryEngine()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = set()


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">📁 Document Management</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, Word, Excel, CSV, TXT",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            with st.spinner("AI Processing documents..."):
                for uploaded_file in uploaded_files:
                    try:
                        metadata = st.session_state.processor.save_file(uploaded_file)
                        
                        documents = st.session_state.processor.load_document(
                            metadata['file_path'],
                            metadata['file_type']
                        )
                        
                        chunks = st.session_state.processor.process_documents(documents, metadata)
                        
                        st.session_state.vector_manager.add_documents(chunks)
                        
                        st.markdown(f'<div class="success-box">✓ Processed: {uploaded_file.name}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="warning-box">✗ Error: {uploaded_file.name}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">📚 Document Library</div>', unsafe_allow_html=True)
        
        all_docs = st.session_state.processor.get_all_metadata()
        
        file_types = list(set([doc['file_type'] for doc in all_docs])) if all_docs else []
        filter_type = st.selectbox("Filter by type", ['all'] + file_types)
        
        filtered_docs = [doc for doc in all_docs if filter_type == 'all' or doc['file_type'] == filter_type]
        
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(filtered_docs)}</div>
                <div class="stat-label">Documents</div>
            </div>
        """, unsafe_allow_html=True)
        
        for doc in filtered_docs:
            with st.expander(f"📄 {doc['filename']}", expanded=False):
                st.markdown(f"""
                    <div class="document-card">
                        <div class="doc-meta">Type: <span class="ai-badge">{doc['file_type'].upper()}</span></div>
                        <div class="doc-meta">Size: {doc['file_size'] / 1024:.2f} KB</div>
                        <div class="doc-meta">Uploaded: {doc['upload_date'][:10]}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    is_selected = doc['file_hash'] in st.session_state.selected_files
                    if st.checkbox("Select", key=f"select_{doc['file_hash']}", value=is_selected):
                        st.session_state.selected_files.add(doc['file_hash'])
                    else:
                        st.session_state.selected_files.discard(doc['file_hash'])
                
                with col2:
                    if st.button("Delete", key=f"del_{doc['file_hash']}", type="secondary", use_container_width=True):
                        st.session_state.processor.delete_document(doc['file_hash'])
                        st.session_state.vector_manager.delete_by_source(doc['file_hash'])
                        st.session_state.selected_files.discard(doc['file_hash'])
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_main_content():
    st.markdown("""
        <div class="hero-section">
            <div class="hero-title">Enterprise RAG System</div>
            <div class="hero-subtitle">Advanced Document Intelligence Platform Powered by Large Language Models</div>
            <span class="ai-badge">Ollama LLM</span>
            <span class="ai-badge">Vector Database</span>
            <span class="ai-badge">Semantic Search</span>
            <span class="ai-badge">Multi-Format Support</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    all_docs = st.session_state.processor.get_all_metadata()
    
    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(all_docs)}</div>
                <div class="stat-label">Total Documents</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len([msg for msg in st.session_state.chat_history if msg['role'] == 'user'])}</div>
                <div class="stat-label">Active Queries</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.selected_files)}</div>
                <div class="stat-label">Selected Documents</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_size = sum([doc['file_size'] for doc in all_docs]) / (1024 * 1024)
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{total_size:.1f}</div>
                <div class="stat-label">Total Storage (MB)</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">AI-Powered Query System</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["💬 Query Interface", "📊 Analytics", "📥 Export"])
    
    with tab1:
        render_query_interface()
    
    with tab2:
        render_analytics()
    
    with tab3:
        render_export_options()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="footer">
            <p><strong>Enterprise RAG System</strong></p>
            <p>Powered by Ollama LLM (llama3:8b) • LangChain • ChromaDB</p>
            <p>Advanced Document Intelligence Platform for Industrial Applications</p>
        </div>
    """, unsafe_allow_html=True)


def render_query_interface():
    if len(st.session_state.selected_files) > 0:
        st.markdown(f'<div class="info-box">🎯 Searching in {len(st.session_state.selected_files)} selected document(s)</div>', unsafe_allow_html=True)
    
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown('<div class="info-box">👋 No queries yet. Upload documents and start asking questions!</div>', unsafe_allow_html=True)
        else:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"""
                        <div class="chat-message">
                            <div class="message-header">
                                <span class="user-badge">USER</span>
                                <span class="timestamp-badge">{message['timestamp']}</span>
                            </div>
                            <div style="color: #cccccc;">{message['content']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="chat-message">
                            <div class="message-header">
                                <span class="assistant-badge">AI ASSISTANT</span>
                                <span class="timestamp-badge">{message['timestamp']}</span>
                            </div>
                            <div style="color: #cccccc; margin-bottom: 1rem;">{message['content']}</div>
                    """, unsafe_allow_html=True)
                    
                    if 'metadata' in message:
                        st.markdown(f"""
                            <div style="margin-top: 1rem;">
                                <span class="confidence-badge">Confidence: {message['metadata']['confidence']:.0%}</span>
                                <span class="source-badge">Sources: {message['metadata']['num_sources']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("📑 View Source Details"):
                            st.markdown('<div class="info-box">', unsafe_allow_html=True)
                            st.markdown("**Sources Used:**")
                            for source in message['metadata']['sources']:
                                st.markdown(f"• {source}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.search_history:
        with st.expander("🕒 Recent Queries", expanded=False):
            for idx, query in enumerate(st.session_state.search_history[:5]):
                if st.button(f"🔍 {query}", key=f"history_{idx}", use_container_width=True):
                    process_query(query)
    
    query_input = st.chat_input("Ask anything about your documents...")
    
    if query_input:
        process_query(query_input)


def process_query(query: str):
    st.session_state.chat_history.append({
        'role': 'user',
        'content': query,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    if query not in st.session_state.search_history:
        st.session_state.search_history.insert(0, query)
        st.session_state.search_history = st.session_state.search_history[:20]
    
    with st.spinner("🤖 AI analyzing documents..."):
        filter_dict = None
        if st.session_state.selected_files:
            filter_dict = {"file_hash": {"$in": list(st.session_state.selected_files)}}
        
        relevant_docs = st.session_state.vector_manager.search(
            query,
            k=5,
            filter_dict=filter_dict
        )
        
        response = st.session_state.query_engine.generate_response(query, relevant_docs)
        
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response['answer'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'metadata': {
                'sources': response['sources'],
                'confidence': response['confidence'],
                'num_sources': response['num_sources']
            }
        })
    
    st.rerun()


def render_analytics():
    st.markdown('<div class="section-header">📊 Document Analytics</div>', unsafe_allow_html=True)
    
    all_docs = st.session_state.processor.get_all_metadata()
    
    if not all_docs:
        st.markdown('<div class="info-box">📂 No documents uploaded yet.</div>', unsafe_allow_html=True)
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Document Types Distribution")
        
        type_counts = {}
        for doc in all_docs:
            doc_type = doc['file_type']
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        df_types = pd.DataFrame(list(type_counts.items()), columns=['Type', 'Count'])
        st.dataframe(df_types, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### Storage Analysis")
        
        storage_by_type = {}
        for doc in all_docs:
            doc_type = doc['file_type']
            size_mb = doc['file_size'] / (1024 * 1024)
            storage_by_type[doc_type] = storage_by_type.get(doc_type, 0) + size_mb
        
        df_storage = pd.DataFrame(
            list(storage_by_type.items()),
            columns=['Type', 'Storage (MB)']
        )
        df_storage['Storage (MB)'] = df_storage['Storage (MB)'].round(2)
        st.dataframe(df_storage, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    st.markdown("#### Query Performance Metrics")
    
    if st.session_state.chat_history:
        assistant_messages = [msg for msg in st.session_state.chat_history if msg['role'] == 'assistant']
        
        if assistant_messages:
            avg_confidence = sum([msg['metadata']['confidence'] for msg in assistant_messages]) / len(assistant_messages)
            avg_sources = sum([msg['metadata']['num_sources'] for msg in assistant_messages]) / len(assistant_messages)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">{len([msg for msg in st.session_state.chat_history if msg['role'] == 'user'])}</div>
                        <div class="stat-label">Total Queries</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">{avg_confidence:.0%}</div>
                        <div class="stat-label">Avg Confidence</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">{avg_sources:.1f}</div>
                        <div class="stat-label">Avg Sources</div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">💡 No queries executed yet.</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("#### Document Timeline")
    
    timeline_data = []
    for doc in all_docs:
        timeline_data.append({
            'Filename': doc['filename'],
            'Type': doc['file_type'],
            'Upload Date': doc['upload_date'][:10],
            'Size (KB)': round(doc['file_size'] / 1024, 2)
        })
    
    df_timeline = pd.DataFrame(timeline_data)
    st.dataframe(df_timeline, use_container_width=True, hide_index=True)


def render_export_options():
    st.markdown('<div class="section-header">📥 Export Options</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export Chat History")
        
        if st.session_state.chat_history:
            export_format = st.radio(
                "Select format:",
                ["Text", "JSON", "CSV"],
                horizontal=True
            )
            
            if st.button("Generate Export", use_container_width=True):
                if export_format == "Text":
                    export_text = "\n\n".join([
                        f"[{msg['timestamp']}] {msg['role'].upper()}:\n{msg['content']}"
                        for msg in st.session_state.chat_history
                    ])
                    
                    st.download_button(
                        "📄 Download Text File",
                        export_text,
                        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                elif export_format == "JSON":
                    export_json = json.dumps(st.session_state.chat_history, indent=2)
                    
                    st.download_button(
                        "📄 Download JSON File",
                        export_json,
                        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                elif export_format == "CSV":
                    df_export = pd.DataFrame([
                        {
                            'Timestamp': msg['timestamp'],
                            'Role': msg['role'],
                            'Content': msg['content'],
                            'Sources': ', '.join(msg.get('metadata', {}).get('sources', [])),
                            'Confidence': msg.get('metadata', {}).get('confidence', 0)
                        }
                        for msg in st.session_state.chat_history
                    ])
                    
                    csv_data = df_export.to_csv(index=False)
                    
                    st.download_button(
                        "📄 Download CSV File",
                        csv_data,
                        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        else:
            st.markdown('<div class="info-box">💬 No chat history to export.</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Export Document Metadata")
        
        all_docs = st.session_state.processor.get_all_metadata()
        
        if all_docs:
            if st.button("Generate Document Report", use_container_width=True):
                df_docs = pd.DataFrame([
                    {
                        'Filename': doc['filename'],
                        'Type': doc['file_type'],
                        'Size (KB)': round(doc['file_size'] / 1024, 2),
                        'Upload Date': doc['upload_date'][:10],
                        'File Hash': doc['file_hash']
                    }
                    for doc in all_docs
                ])
                
                csv_data = df_docs.to_csv(index=False)
                
                st.download_button(
                    "📄 Download Document Report",
                    csv_data,
                    file_name=f"document_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.markdown('<div class="info-box">📂 No documents to export.</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("#### Batch Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.search_history = []
            st.markdown('<div class="success-box">✓ Chat history cleared!</div>', unsafe_allow_html=True)
            st.rerun()
    
    with col2:
        if st.button("🔄 Clear Selection", type="secondary", use_container_width=True):
            st.session_state.selected_files = set()
            st.markdown('<div class="success-box">✓ Selection cleared!</div>', unsafe_allow_html=True)
            st.rerun()
    
    with col3:
        all_docs = st.session_state.processor.get_all_metadata()
        if all_docs:
            if st.button("⚠️ Delete All Documents", type="secondary", use_container_width=True):
                for doc in all_docs:
                    st.session_state.processor.delete_document(doc['file_hash'])
                    st.session_state.vector_manager.delete_by_source(doc['file_hash'])
                
                st.session_state.selected_files = set()
                st.session_state.chat_history = []
                st.markdown('<div class="success-box">✓ All documents deleted!</div>', unsafe_allow_html=True)
                st.rerun()


def main():
    apply_enhanced_styles()
    
    init_session_state()
    
    render_sidebar()
    
    render_main_content()
    
    with st.sidebar:
        st.markdown("---")
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">ℹ️ System Information</div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="info-box">
                <div style="margin: 0.5rem 0;"><strong>Version:</strong> 1.0.0</div>
                <div style="margin: 0.5rem 0;"><strong>Model:</strong> llama3:8b</div>
                <div style="margin: 0.5rem 0;"><strong>Embedding:</strong> OllamaEmbeddings</div>
                <div style="margin: 0.5rem 0;"><strong>Status:</strong> <span class="ai-badge">Active</span></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()