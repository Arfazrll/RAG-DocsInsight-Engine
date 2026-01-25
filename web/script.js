
document.addEventListener('DOMContentLoaded', () => {
    const fileUpload = document.getElementById('file-upload');
    const uploadStatus = document.getElementById('upload-status');
    const documentList = document.getElementById('document-list');
    const docCount = document.getElementById('doc-count');
    const chatContainer = document.getElementById('chat-container');
    const queryInput = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');

    let selectedFiles = new Set();

    // Configure Marked.js
    marked.setOptions({
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        },
        langPrefix: 'hljs language-'
    });

    // Auto-resize textarea
    queryInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = 'auto';
    });

    // Initial Load
    loadDocuments();

    // File Upload Handling
    fileUpload.addEventListener('change', async (e) => {
        const files = e.target.files;
        if (files.length === 0) return;

        uploadStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('file', files[i]);
        }

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            loadDocuments();
            uploadStatus.style.color = '#10b981';
            uploadStatus.innerHTML = `<i class="fas fa-check"></i> Uploaded ${result.results.length} files`;
            setTimeout(() => {
                uploadStatus.innerHTML = '';
            }, 3000);
        } catch (error) {
            console.error('Error:', error);
            uploadStatus.style.color = '#ef4444';
            uploadStatus.textContent = 'Upload failed';
        }
    });

    // Load Documents
    async function loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            const documents = await response.json();

            docCount.textContent = documents.length;
            documentList.innerHTML = '';

            documents.forEach(doc => {
                const card = document.createElement('div');
                card.className = 'doc-card glass-card';

                const isSelected = selectedFiles.has(doc.file_hash);

                card.innerHTML = `
                    <div class="doc-header">
                        <div style="display:flex;align-items:center;flex:1;overflow:hidden">
                            <input type="checkbox" class="selection-checkbox" 
                                data-hash="${doc.file_hash}" ${isSelected ? 'checked' : ''} style="margin-right:10px;accent-color:var(--accent-primary)">
                            <div class="doc-title" title="${doc.filename}" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                                <i class="far fa-file-alt" style="margin-right:6px;color:var(--accent-secondary)"></i>
                                ${doc.filename}
                            </div>
                        </div>
                        <button class="delete-btn" onclick="deleteDocument('${doc.file_hash}')" title="Delete">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="doc-meta">
                        <span style="text-transform:uppercase;font-size:0.6rem;letter-spacing:1px;font-weight:700">${doc.file_type}</span>
                        <span>${(doc.file_size / 1024).toFixed(1)} KB</span>
                    </div>
                `;
                documentList.appendChild(card);
            });

            document.querySelectorAll('.selection-checkbox').forEach(cb => {
                cb.addEventListener('change', (e) => {
                    const hash = e.target.dataset.hash;
                    if (e.target.checked) {
                        selectedFiles.add(hash);
                    } else {
                        selectedFiles.delete(hash);
                    }
                });
            });

        } catch (error) {
            console.error('Error loading documents:', error);
        }
    }

    // Delete Document
    window.deleteDocument = async (fileHash) => {
        if (!confirm('Permanently delete this document?')) return;

        try {
            await fetch(`/api/documents/${fileHash}`, {
                method: 'DELETE'
            });
            selectedFiles.delete(fileHash);
            loadDocuments();
        } catch (error) {
            console.error('Error deleting document:', error);
        }
    };

    // Chat Functionality
    async function sendMessage() {
        const query = queryInput.value.trim();
        if (!query) return;

        // Disable Input
        queryInput.disabled = true;
        sendBtn.disabled = true;

        // Add User Message
        appendMessage('user', query);
        queryInput.value = '';
        queryInput.style.height = 'auto'; // Reset height

        // Show Loading
        const loadingId = appendLoading();

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    selected_files: Array.from(selectedFiles)
                })
            });

            const data = await response.json();

            // Remove Loading
            document.getElementById(loadingId).remove();

            // Add Assistant Message
            appendMessage('assistant', data.answer, data);

        } catch (error) {
            console.error('Error:', error);
            document.getElementById(loadingId).remove();
            appendMessage('assistant', '__Error__: Sorry, I encountered an error processing your request.');
        } finally {
            queryInput.disabled = false;
            sendBtn.disabled = false;
            queryInput.focus();
        }
    }

    function appendMessage(role, content, metadata = null) {
        const div = document.createElement('div');
        div.className = `chat-message ${role}`;

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        let sourcesHtml = '';
        if (metadata && metadata.sources && metadata.sources.length > 0) {
            sourcesHtml = `
                <div class="sources-section">
                    <div class="sources-title"><i class="fas fa-quote-right"></i> Sources Referenced</div>
                    <div>
                        ${metadata.sources.map(s => `<span class="source-tag">${s}</span>`).join('')}
                    </div>
                </div>
            `;
        }

        // Parse Markdown if assistant
        const formattedContent = role === 'assistant' ? marked.parse(content) : content;

        div.innerHTML = `
            <div class="role-badge">
                <i class="fas ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i>
                ${role === 'user' ? 'YOU' : 'AI ASSISTANT'}
                <span style="margin-left:auto;font-weight:400;opacity:0.7">${timestamp}</span>
            </div>
            <div class="message-content">${formattedContent}</div>
            ${sourcesHtml}
        `;

        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        const emptyState = document.querySelector('.empty-state');
        if (emptyState) emptyState.style.display = 'none';

        // Re-highlight code blocks
        if (role === 'assistant') {
            div.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    }

    function appendLoading() {
        const id = 'loading-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'chat-message assistant';
        div.innerHTML = `
            <div class="role-badge">
                <i class="fas fa-robot"></i> AI ASSISTANT
            </div>
            <div class="message-content">
                <i class="fas fa-circle-notch fa-spin" style="color:var(--accent-primary)"></i> 
                <span class="typing-text">Analyzing documents...</span>
            </div>
        `;
        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return id;
    }

    sendBtn.addEventListener('click', sendMessage);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
