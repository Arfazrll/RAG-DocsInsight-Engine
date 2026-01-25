
import os
import json
import hashlib
import shutil
from datetime import datetime
from typing import List, Dict, Optional
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
    
    def save_file(self, file_storage) -> Dict:
        file_bytes = file_storage.read()
        file_storage.seek(0) 
        
        file_hash = self.generate_file_hash(file_bytes)
        original_filename = file_storage.filename
        file_ext = original_filename.split('.')[-1].lower()
        
        file_path = os.path.join(self.docs_path, f"{file_hash}.{file_ext}")
        
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
        
        metadata = {
            'filename': original_filename,
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
        
        if not os.path.exists(self.metadata_path):
            return []
            
        for filename in os.listdir(self.metadata_path):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.metadata_path, filename), 'r') as f:
                        metadata_list.append(json.load(f))
                except Exception:
                    continue
        
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
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.embedding_function = OllamaEmbeddings(model=embedding_model, base_url=base_url)
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
        if not documents:
            return
            
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
        
        if self.vector_store._collection.count() == 0:
            return []

        if filter_dict:
            return self.vector_store.similarity_search(query, k=k, filter=filter_dict)
        else:
            return self.vector_store.similarity_search(query, k=k)
    
    def delete_by_source(self, file_hash: str):
        if self.vector_store:
            try:
                self.vector_store.delete(where={"file_hash": file_hash})
            except Exception as e:
                print(f"Error deleting from vector store: {e}")


class RAGQueryEngine:
    
    def __init__(self, model_name: str = "llama3:8b"):
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.llm = OllamaLLM(model=model_name, temperature=0.7, base_url=base_url)
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
