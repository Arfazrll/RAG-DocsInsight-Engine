document.addEventListener('DOMContentLoaded', () => {

    // ═══════ LANDING PAGE LOGIC ═══════

    // Navbar scroll effect
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 20);
        });
    }

    // Mobile nav toggle
    const mobileToggle = document.getElementById('nav-mobile-toggle');
    const navLinks = document.getElementById('nav-links');
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });
        navLinks.querySelectorAll('a').forEach(a => {
            a.addEventListener('click', () => navLinks.classList.remove('open'));
        });
    }

    // Scroll reveal
    const reveals = document.querySelectorAll('.reveal');
    if (reveals.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, i) => {
                if (entry.isIntersecting) {
                    setTimeout(() => entry.target.classList.add('visible'), i * 60);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });
        reveals.forEach(el => observer.observe(el));
    }

    // FAQ accordion
    document.querySelectorAll('.faq-q').forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.parentElement;
            const wasOpen = item.classList.contains('open');
            document.querySelectorAll('.faq-item.open').forEach(el => el.classList.remove('open'));
            if (!wasOpen) item.classList.add('open');
        });
    });

    // Launch app buttons
    const appView = document.getElementById('app-view');
    const landingPage = document.getElementById('landing-page');

    function openApp() {
        if (!appView || !landingPage) return;
        appView.classList.remove('hidden');
        requestAnimationFrame(() => appView.classList.add('visible'));
        document.body.style.overflow = 'hidden';
        loadDocuments();
    }

    function closeApp() {
        if (!appView || !landingPage) return;
        appView.classList.remove('visible');
        setTimeout(() => appView.classList.add('hidden'), 350);
        document.body.style.overflow = '';
    }

    document.getElementById('btn-launch-hero')?.addEventListener('click', openApp);
    document.getElementById('btn-launch-nav')?.addEventListener('click', openApp);
    document.getElementById('btn-back')?.addEventListener('click', closeApp);

    // ═══════ APP LOGIC ═══════

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

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
    }

    let selectedFiles = new Set();

    marked.setOptions({
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        },
        langPrefix: 'hljs language-'
    });

    if (queryInput) {
        queryInput.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
            if (this.value === '') this.style.height = 'auto';
        });
    }

    // Drag & drop
    if (dropZone) {
        ['dragenter', 'dragover'].forEach(evt => {
            dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
        });
        ['dragleave', 'drop'].forEach(evt => {
            dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove('drag-over'); });
        });
        dropZone.addEventListener('drop', e => {
            const files = e.dataTransfer.files;
            if (files.length > 0) { fileUpload.files = files; fileUpload.dispatchEvent(new Event('change')); }
        });
    }

    // Suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const q = chip.dataset.query;
            if (q && queryInput) { queryInput.value = q; queryInput.dispatchEvent(new Event('input')); sendMessage(); }
        });
    });

    // Upload
    if (fileUpload) {
        fileUpload.addEventListener('change', async (e) => {
            const files = e.target.files;
            if (files.length === 0) return;
            uploadStatus.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Uploading...';
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) formData.append('file', files[i]);
            try {
                const response = await fetch('/api/upload', { method: 'POST', body: formData });
                const result = await response.json();
                loadDocuments();
                uploadStatus.style.color = 'var(--gray-300)';
                uploadStatus.innerHTML = `${result.results.length} file(s) uploaded`;
                setTimeout(() => { uploadStatus.innerHTML = ''; }, 3000);
            } catch (error) {
                console.error('Error:', error);
                uploadStatus.style.color = 'var(--gray-400)';
                uploadStatus.textContent = 'Upload failed';
            }
        });
    }

    async function loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            const documents = await response.json();
            if (docCount) docCount.textContent = documents.length;
            if (!documentList) return;
            documentList.innerHTML = '';
            documents.forEach(doc => {
                const card = document.createElement('div');
                card.className = 'doc-card';
                const isSelected = selectedFiles.has(doc.file_hash);
                const ft = doc.file_type.toLowerCase();
                card.innerHTML = `
                    <div class="doc-header">
                        <input type="checkbox" class="selection-checkbox" data-hash="${doc.file_hash}" ${isSelected ? 'checked' : ''} style="accent-color:var(--gray-300);cursor:pointer;flex-shrink:0">
                        <div class="doc-title" title="${doc.filename}">${doc.filename}</div>
                        <button class="delete-btn" onclick="deleteDocument('${doc.file_hash}')" title="Delete"><i class="fas fa-xmark"></i></button>
                    </div>
                    <div class="doc-meta">
                        <span class="file-type-badge">${ft}</span>
                        <span>${(doc.file_size / 1024).toFixed(1)} KB</span>
                    </div>`;
                documentList.appendChild(card);
            });
            document.querySelectorAll('.selection-checkbox').forEach(cb => {
                cb.addEventListener('change', e => {
                    const hash = e.target.dataset.hash;
                    e.target.checked ? selectedFiles.add(hash) : selectedFiles.delete(hash);
                });
            });
        } catch (error) { console.error('Error loading documents:', error); }
    }

    window.deleteDocument = async (fileHash) => {
        if (!confirm('Permanently delete this document?')) return;
        try {
            await fetch(`/api/documents/${fileHash}`, { method: 'DELETE' });
            selectedFiles.delete(fileHash);
            loadDocuments();
        } catch (error) { console.error('Error deleting document:', error); }
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
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, selected_files: Array.from(selectedFiles) })
            });
            const data = await response.json();
            document.getElementById(loadingId).remove();
            appendMessage('assistant', data.answer, data);
        } catch (error) {
            console.error('Error:', error);
            document.getElementById(loadingId).remove();
            appendMessage('assistant', 'Error: Could not process your request.');
        } finally {
            queryInput.disabled = false;
            sendBtn.disabled = false;
            queryInput.focus();
        }
    }

    function appendMessage(role, content, metadata = null) {
        const div = document.createElement('div');
        div.className = `chat-message ${role}`;
        const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        let srcHtml = '';
        if (metadata?.sources?.length > 0) {
            srcHtml = `<div class="sources-section"><div class="sources-title"><i class="fas fa-quote-right"></i> Sources</div><div>${metadata.sources.map(s => `<span class="source-tag">${s}</span>`).join('')}</div></div>`;
        }
        const formatted = role === 'assistant' ? marked.parse(content) : content;
        div.innerHTML = `
            <div class="role-badge"><i class="fas ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i> ${role === 'user' ? 'You' : 'Assistant'} <span style="margin-left:auto;opacity:0.5;font-size:10px">${ts}</span></div>
            <div class="message-content">${formatted}</div>${srcHtml}`;
        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        const empty = document.querySelector('.empty-state');
        if (empty) empty.style.display = 'none';
        if (role === 'assistant') div.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
    }

    function appendLoading() {
        const id = 'loading-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'chat-message assistant';
        div.innerHTML = `<div class="role-badge"><i class="fas fa-robot"></i> Assistant</div><div class="message-content" style="display:flex;align-items:center;gap:8px"><div class="loading-dots"><span></span><span></span><span></span></div><span style="color:var(--gray-500);font-size:13px">Thinking...</span></div>`;
        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return id;
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (queryInput) {
        queryInput.addEventListener('keypress', e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });
    }
});
