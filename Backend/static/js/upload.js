/**
 * SAV.IN Upload Module
 * Handles PDF upload with drag-and-drop, progress tracking, and document management
 */

class UploadManager {
    constructor() {
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.browseButton = document.getElementById('browseButton');
        this.refreshButton = document.getElementById('refreshBtn');
        this.documentsList = document.getElementById('documentsList');
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadDocuments();
        this.startPolling();
    }
    
    setupEventListeners() {
        // Browse button click
        this.browseButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.fileInput.click();
        });
        
        // Upload area click (excluding browse button)
        this.uploadArea.addEventListener('click', (e) => {
            if (!e.target.closest('#browseButton')) {
                this.fileInput.click();
            }
        });
        
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
        
        // Drag and drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.add('drag-over');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.remove('drag-over');
            }, false);
        });
        
        this.uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        }, false);
        
        // Refresh button
        this.refreshButton.addEventListener('click', () => {
            this.loadDocuments();
        });
        
        // Suggested questions
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const question = chip.getAttribute('data-question');
                this.sendSuggestion(question);
            });
        });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    async handleFileUpload(file) {
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }
        
        // Show progress
        this.showUploadProgress(file);
        
        try {
            // Create FormData
            const formData = new FormData();
            formData.append('file', file);
            
            // Upload file
            const response = await apiRequest('/document/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.success) {
                showNotification('Document uploaded successfully!', 'success');
                this.hideUploadProgress();
                
                // Start monitoring processing
                this.monitorDocumentProcessing(response.data.id);
                
                // Reload documents after a short delay
                setTimeout(() => this.loadDocuments(), 1000);
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            showNotification(`Upload failed: ${error.message}`, 'error');
            this.hideUploadProgress();
        }
    }
    
    validateFile(file) {
        // Check file type
        if (!file.type.includes('pdf')) {
            showNotification('Please select a PDF file', 'error');
            return false;
        }
        
        // Check file size (16MB limit)
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            showNotification('File size must be less than 16MB', 'error');
            return false;
        }
        
        // Check file name
        if (!file.name || file.name.trim() === '') {
            showNotification('Invalid file name', 'error');
            return false;
        }
        
        return true;
    }
    
    showUploadProgress(file) {
        const placeholder = document.getElementById('uploadPlaceholder');
        const progress = document.getElementById('uploadProgress');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        // Update file info
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        
        // Show progress UI
        placeholder.classList.add('hidden');
        progress.classList.remove('hidden');
        
        // Animate progress
        let progressValue = 0;
        const interval = setInterval(() => {
            progressValue += Math.random() * 10 + 5;
            
            if (progressValue >= 100) {
                progressValue = 100;
                clearInterval(interval);
                progressText.textContent = 'Processing document...';
            } else {
                progressText.textContent = `Uploading... ${Math.round(progressValue)}%`;
            }
            
            progressFill.style.width = `${progressValue}%`;
        }, 200);
    }
    
    hideUploadProgress() {
        const placeholder = document.getElementById('uploadPlaceholder');
        const progress = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        
        // Reset progress
        progressFill.style.width = '0%';
        
        // Show placeholder
        placeholder.classList.remove('hidden');
        progress.classList.add('hidden');
        
        // Reset file input
        this.fileInput.value = '';
    }
    
    async monitorDocumentProcessing(documentId) {
        const pollInterval = 2000; // 2 seconds
        let attempts = 0;
        const maxAttempts = 30; // 60 seconds total
        
        const poll = async () => {
            try {
                attempts++;
                const response = await apiRequest(`/document/${documentId}`);
                
                if (response.success) {
                    const doc = response.data;
                    
                    if (doc.status === 'completed') {
                        showNotification('Document processed and ready for chat!', 'success');
                        this.loadDocuments();
                        return;
                    }
                    
                    if (doc.status === 'error') {
                        showNotification(`Processing failed: ${doc.error_message}`, 'error');
                        this.loadDocuments();
                        return;
                    }
                    
                    if (attempts < maxAttempts && doc.status === 'processing') {
                        setTimeout(poll, pollInterval);
                    }
                }
            } catch (error) {
                console.error('Polling error:', error);
                if (attempts < maxAttempts) {
                    setTimeout(poll, pollInterval);
                }
            }
        };
        
        setTimeout(poll, pollInterval);
    }
    
    async loadDocuments() {
        try {
            const response = await apiRequest('/document/list');
            
            if (response.success) {
                this.renderDocuments(response.data);
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            console.error('Failed to load documents:', error);
            this.renderError('Failed to load documents');
        }
    }
    
    renderDocuments(documents) {
        if (!documents || documents.length === 0) {
            this.renderEmptyState();
            return;
        }
        
        const documentsHtml = documents.map(doc => this.createDocumentHTML(doc)).join('');
        this.documentsList.innerHTML = documentsHtml;
        
        // Add event listeners
        this.addDocumentEventListeners();
    }
    
    createDocumentHTML(doc) {
        const statusClass = `status-${doc.status}`;
        const isCompleted = doc.status === 'completed';
        const isProcessing = doc.status === 'processing';
        
        let progressHtml = '';
        if (isProcessing) {
            progressHtml = `
                <div class="mini-progress">
                    <div style="width: ${doc.processing_progress || 0}%"></div>
                </div>
            `;
        }
        
        return `
            <div class="document-item" data-id="${doc.id}" data-status="${doc.status}">
                <div class="document-icon">
                    <i class="material-icons">picture_as_pdf</i>
                </div>
                <div class="document-details">
                    <h4>${doc.filename}</h4>
                    <p>
                        <i class="material-icons">data_usage</i>
                        ${doc.file_size} MB • ${doc.chunk_count || 0} chunks
                    </p>
                    <small>
                        <i class="material-icons">schedule</i>
                        ${formatDate(doc.created_at)}
                    </small>
                </div>
                <div class="document-status">
                    <span class="status-badge ${statusClass}">
                        ${doc.status}
                    </span>
                    ${progressHtml}
                </div>
                <div class="document-actions">
                    ${isCompleted ? `
                        <button class="action-btn primary" onclick="uploadManager.startChat(${doc.id})" title="Start Chat">
                            <i class="material-icons">chat</i>
                        </button>
                    ` : ''}
                    <button class="action-btn danger" onclick="uploadManager.deleteDocument(${doc.id})" title="Delete Document">
                        <i class="material-icons">delete</i>
                    </button>
                </div>
            </div>
        `;
    }
    
    addDocumentEventListeners() {
        // Add click handlers for document selection
        const documentItems = this.documentsList.querySelectorAll('.document-item');
        documentItems.forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.document-actions')) {
                    const documentId = item.getAttribute('data-id');
                    const status = item.getAttribute('data-status');
                    
                    if (status === 'completed') {
                        this.startChat(parseInt(documentId));
                    } else {
                        showNotification(`Document is ${status}. Please wait for processing to complete.`, 'warning');
                    }
                }
            });
        });
    }
    
    renderEmptyState() {
        this.documentsList.innerHTML = `
            <div class="empty-state">
                <i class="material-icons">description</i>
                <h4>No documents uploaded yet</h4>
                <p>Upload your first PDF to get started with AI-powered conversations</p>
                <small>Supported format: PDF (max 16MB)</small>
            </div>
        `;
    }
    
    renderError(message) {
        this.documentsList.innerHTML = `
            <div class="empty-state">
                <i class="material-icons">error</i>
                <h4>Error</h4>
                <p>${message}</p>
                <small>Please try refreshing the page</small>
            </div>
        `;
    }
    
    async startChat(documentId) {
        try {
            showNotification('Creating chat session...', 'info');
            
            const response = await apiRequest('/chat/create', {
                method: 'POST',
                body: JSON.stringify({ 
                    document_id: documentId,
                    title: `Chat with Document #${documentId}`
                })
            });
            
            if (response.success) {
                // Store chat info for the chat page
                sessionStorage.setItem('currentChat', JSON.stringify({
                    chatId: response.data.id,
                    documentId: documentId,
                    title: response.data.title
                }));
                
                // Navigate to chat page
                window.location.href = `/chat?chat_id=${response.data.id}&doc_id=${documentId}`;
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            console.error('Chat creation error:', error);
            showNotification(`Failed to start chat: ${error.message}`, 'error');
        }
    }
    
    async deleteDocument(documentId) {
        if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await apiRequest(`/document/${documentId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                showNotification('Document deleted successfully', 'success');
                this.loadDocuments();
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            console.error('Delete error:', error);
            showNotification(`Delete failed: ${error.message}`, 'error');
        }
    }
    
    startPolling() {
        // Poll for document updates every 5 seconds
        setInterval(() => {
            const processingDocs = this.documentsList.querySelectorAll('[data-status="processing"]');
            if (processingDocs.length > 0) {
                this.loadDocuments();
            }
        }, 5000);
    }
    
    sendSuggestion(question) {
        // Store the suggested question and navigate to chat
        sessionStorage.setItem('suggestedQuestion', question);
        showNotification('Select a document to ask this question', 'info');
    }
}

// Initialize upload manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.uploadManager = new UploadManager();
});
