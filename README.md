# 🧠 DocsInsight Engine: Enterprise RAG System

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Enabled-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-white?style=for-the-badge&logo=ollama&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

**DocsInsight Engine** is a high-performance, private Retrieval-Augmented Generation (RAG) platform. It allows users to upload complex documents and interact with them through a neural search interface powered by local Large Language Models (LLMs).

---

## ✨ Key Features

- 📁 **Multi-Format Support**: Seamlessly process PDF, DOCX, XLSX, CSV, and TXT files.
- 🔒 **Privacy-Centric**: Fully local execution using **Ollama**. Your sensitive data never leaves your infrastructure.
- ⚡ **Neural Retrieval**: Uses **ChromaDB** for high-speed vector similarity search.
- 🎨 **Modern Interface**: A sleek, dark-themed "Glassmorphism" UI with real-time markdown rendering and code highlighting.
- 🛠️ **Source Verification**: Every answer comes with citations from the uploaded documents to prevent hallucinations.
- 🐳 **One-Command Setup**: Ready for production with Docker and Docker Compose.

---

## 🏗️ Technical Architecture

### **Backend Stack**
- **Core**: Python 3.11 with Flask.
- **Orchestration**: LangChain for managing document loaders, splitters, and LLM chains.
- **Vector Database**: ChromaDB for persistent document embeddings.
- **LLM/Embeddings**: Llama 3 (8B) via Ollama.

### **Frontend Stack**
- **UI**: Vanilla JS with CSS Mesh Gradients and Backdrop Filters.
- **Rendering**: Marked.js for markdown and Highlight.js for code snippets.

---

## 🚀 Getting Started

### Prerequisites
- [Docker](https://www.docker.com/) and Docker Compose.
- [Ollama](https://ollama.com/) installed and running on your host machine.
- Pull the required model: `ollama pull llama3:8b`.

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/arfazrll/rag-docsinsight-engine.git](https://github.com/arfazrll/rag-docsinsight-engine.git)
   cd rag-docsinsight-engine

2. **Launch with Docker:**
    ```bash
    docker-compose up --build

3. **Access the App:**
   Open your browser and navigate to `http://localhost:5000`.

---

## 📂 Project Structure

```text
├── backend/
│   ├── app.py          # Flask API Endpoints
│   └── rag_core.py     # RAG Logic, Vector Store & Document Processing
├── web/
│   ├── index.html      # Frontend Structure
│   ├── style.css       # Glassmorphism Styling
│   └── script.js       # Client-side Logic
├── storage/            # Local Persistent Storage (Vector DB & Docs)
├── Dockerfile          # Container Configuration
└── docker-compose.yml  # Service Orchestration

```

---

## 🛠️ Configuration

The system uses environment variables to communicate with the AI engine. In `docker-compose.yml`:

* `Ollama_BASE_URL`: Defaults to `http://host.docker.internal:11434` for local communication.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

Copyright (c) 2025 **S. A. Almazril**.

---

## 💡 System Insights

* **Scalability**: The `VectorStoreManager` is designed to handle multiple documents simultaneously by filtering searches based on unique file hashes.
* **Performance**: Document chunking is optimized with a `1000` character size and `200` character overlap to maintain context window efficiency.
* **Security**: Includes a `.dockerignore` and `.gitignore` to prevent sensitive credentials (`.env`) or local databases from being leaked.
