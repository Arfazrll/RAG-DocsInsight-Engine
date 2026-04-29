
document.addEventListener('DOMContentLoaded', () => {
    const fileUpload = document.getElementById('file-upload');
    const uploadStatus = document.getElementById('upload-status');
    const documentList = document.getElementById('document-list');
    const docCount = document.getElementById('doc-count');
    const chatContainer = document.getElementById('chat-container');
    const queryInput = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const dropZone = document.getElementById('drop-zone');

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    let selectedFiles = new Set();

    marked.setOptions({
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        },
        langPrefix: 'hljs language-'
    });

    queryInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = 'auto';
    });

    // Drag & drop
    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileUpload.files = files;
            fileUpload.dispatchEvent(new Event('change'));
        }
    });

    // Suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.dataset.query;
            if (query) {
                queryInput.value = query;
                queryInput.dispatchEvent(new Event('input'));
                sendMessage();
            }
        });
    });

    loadDocuments();

    fileUpload.addEventListener('change', async (e) => {
        const files = e.target.files;
        if (files.length === 0) return;

        uploadStatus.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Uploading...';

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
            uploadStatus.style.color = 'var(--accent-secondary)';
            uploadStatus.innerHTML = `<i class="fas fa-check-circle"></i> ${result.results.length} file(s) uploaded`;
            setTimeout(() => {
                uploadStatus.innerHTML = '';
            }, 3000);
        } catch (error) {
            console.error('Error:', error);
            uploadStatus.style.color = '#f87171';
            uploadStatus.textContent = 'Upload failed';
        }
    });

    async function loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            const documents = await response.json();

            docCount.textContent = documents.length;
            documentList.innerHTML = '';

            documents.forEach((doc, index) => {
                const card = document.createElement('div');
                card.className = 'doc-card';
                card.style.animationDelay = `${index * 0.05}s`;

                const isSelected = selectedFiles.has(doc.file_hash);
                const ft = doc.file_type.toLowerCase();

                card.innerHTML = `
                    <div class="doc-header">
                        <div style="display:flex;align-items:center;flex:1;overflow:hidden;gap:8px">
                            <input type="checkbox" class="selection-checkbox" 
                                data-hash="${doc.file_hash}" ${isSelected ? 'checked' : ''} style="accent-color:var(--accent-primary);cursor:pointer;flex-shrink:0">
                            <div class="doc-title" title="${doc.filename}" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                                ${doc.filename}
                            </div>
                        </div>
                        <button class="delete-btn" onclick="deleteDocument('${doc.file_hash}')" title="Delete">
                            <i class="fas fa-trash-can" style="font-size:0.7rem"></i>
                        </button>
                    </div>
                    <div class="doc-meta">
                        <span class="file-type-badge ${ft}">${ft}</span>
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

    async function sendMessage() {
        const query = queryInput.value.trim();
        if (!query) return;

        queryInput.disabled = true;
        sendBtn.disabled = true;

        appendMessage('user', query);
        queryInput.value = '';
        queryInput.style.height = 'auto';

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

            document.getElementById(loadingId).remove();

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

        const formattedContent = role === 'assistant' ? marked.parse(content) : content;

        div.innerHTML = `
            <div class="role-badge">
                <i class="fas ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i>
                ${role === 'user' ? 'YOU' : 'AI ASSISTANT'}
                <span style="margin-left:auto;font-weight:400;opacity:0.5;font-size:0.6rem">${timestamp}</span>
            </div>
            <div class="message-content">${formattedContent}</div>
            ${sourcesHtml}
        `;

        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        const emptyState = document.querySelector('.empty-state');
        if (emptyState) emptyState.style.display = 'none';

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
            <div class="message-content" style="display:flex;align-items:center;gap:10px">
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
                <span style="color:var(--text-muted);font-size:0.85rem">Analyzing documents...</span>
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
