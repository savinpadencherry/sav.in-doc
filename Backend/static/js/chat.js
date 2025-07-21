/**
 * SAV.IN Chat Controller
 * Handles real-time chat with PDF documents
 */

class ChatManager {
    constructor() {
        // State management
        this.currentChatId = null;
        this.currentDocumentId = null;
        this.isTyping = false;
        
        // DOM Elements
        this.documentsList = document.getElementById('documentsList');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendBtn');
        this.documentTitle = document.getElementById('documentTitle');
        this.documentMeta = document.getElementById('documentMeta');
        this.docSearch = document.getElementById('docSearch');
        
        // Action buttons
        this.viewPdfBtn = document.getElementById('viewPdfBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.clearChatBtn = document.getElementById('clearChatBtn');
    }
    
    init() {
        this.setupEventListeners();
        this.loadDocuments();
        this.initializeFromURL();
        this.setWelcomeTime();
    }
    
    setupEventListeners() {
        // Message input handlers
        this.messageInput.addEventListener('input', () => this.updateSendButton());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Document search
        this.docSearch.addEventListener('input', (e) => {
            this.filterDocuments(e.target.value);
        });
        
        // Suggested questions
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const question = chip.getAttribute('data-question');
                this.sendSuggestion(question);
            });
        });
        
        // Action buttons
        this.viewPdfBtn.addEventListener('click', () => this.viewPdf());
        this.downloadBtn.addEventListener('click', () => this.downloadPdf());
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
    }
    
    async loadDocuments() {
        try {
            // Show loading state
            this.documentsList.innerHTML = `
                <div class="loading-placeholder">
                    <div class="spinner"></div>
                    <p>Loading documents...</p>
                </div>
            `;
            
            const response = await apiRequest('/document/list');
            
            if (response.success) {
                this.renderDocumentList(response.data);
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            console.error('Failed to load documents:', error);
            this.renderDocumentError('Failed to load documents');
        }
    }
    
    renderDocumentList(documents) {
        if (!documents || documents.length === 0) {
            this.renderEmptyDocuments();
            return;
        }
        
        // Filter for completed documents
        const completedDocs = documents.filter(doc => doc.status === 'completed');
        
        if (completedDocs.length === 0) {
            this.documentsList.innerHTML = `
                <div class="empty-state">
                    <i class="material-icons">hourglass_empty</i>
                    <h4>No documents ready</h4>
                    <p>Your documents are still processing</p>
                    <small>Check back in a few moments</small>
                </div>
            `;
            return;
        }
        
        this.documentsList.innerHTML = completedDocs.map(doc => `
            <div class="document-item" 
                 data-id="${doc.id}" 
                 data-filename="${doc.filename}">
                <div class="document-icon">
                    <i class="material-icons">picture_as_pdf</i>
                </div>
                <div class="document-details">
                    <h4>${doc.filename}</h4>
                    <p>${doc.file_size} MB • ${doc.chunk_count || 0} chunks</p>
                </div>
                <div class="document-status">
                    <span class="status-badge status-completed">Ready</span>
                </div>
            </div>
        `).join('');
        
        // Add event listeners
        this.addDocumentListeners();
        
        // Highlight current document
        if (this.currentDocumentId) {
            this.highlightCurrentDocument();
        }
    }
    
    addDocumentListeners() {
        const documentItems = this.documentsList.querySelectorAll('.document-item');
        documentItems.forEach(item => {
            item.addEventListener('click', () => {
                const documentId = item.getAttribute('data-id');
                const filename = item.getAttribute('data-filename');
                this.selectDocument(parseInt(documentId), filename);
            });
        });
    }
    
    renderEmptyDocuments() {
        this.documentsList.innerHTML = `
            <div class="empty-state">
                <i class="material-icons">description</i>
                <h4>No documents available</h4>
                <p>Upload a PDF document first to start chatting</p>
                <small>Go to the Upload page to add documents</small>
            </div>
        `;
    }
    
    renderDocumentError(message) {
        this.documentsList.innerHTML = `
            <div class="empty-state">
                <i class="material-icons">error</i>
                <h4>Error loading documents</h4>
                <p>${message}</p>
                <small>Please try refreshing the page</small>
            </div>
        `;
    }
    
    initializeFromURL() {
        // Get URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const chatId = urlParams.get('chat_id');
        const docId = urlParams.get('doc_id');
        
        if (chatId && docId) {
            this.currentChatId = parseInt(chatId);
            this.currentDocumentId = parseInt(docId);
            this.loadChatSession();
        }
    }
    
    async selectDocument(documentId, filename) {
        try {
            // Remove previous selection
            this.documentsList.querySelectorAll('.document-item').forEach(item => {
                item.classList.remove('selected');
            });
            
            // Add selection to current item
            const selectedItem = this.documentsList.querySelector(`[data-id="${documentId}"]`);
            if (selectedItem) {
                selectedItem.classList.add('selected');
            }
            
            // Update document info in header
            this.documentTitle.textContent = filename;
            this.documentMeta.textContent = 'Loading document details...';
            
            // Create or load chat session
            await this.createOrLoadChat(documentId);
            
        } catch (error) {
            console.error('Failed to select document:', error);
            showNotification('Failed to select document', 'error');
        }
    }
    
    async createOrLoadChat(documentId) {
        try {
            showNotification('Preparing chat session...', 'info');
            
            // Create new chat session
            const response = await apiRequest('/chat/create', {
                method: 'POST',
                body: JSON.stringify({ 
                    document_id: documentId,
                    title: `Chat with ${this.documentTitle.textContent}`
                })
            });
            
            if (response.success) {
                this.loadChatSession(response.data.id, documentId);
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            console.error('Chat initialization failed:', error);
            showNotification(`Failed to start chat: ${error.message}`, 'error');
        }
    }
    
    async loadChatSession(chatId, documentId) {
        try {
            // Set current IDs
            this.currentChatId = chatId;
            this.currentDocumentId = documentId;
            
            // Update URL
            window.history.replaceState(
                {}, 
                '', 
                `/chat?chat_id=${chatId}&doc_id=${documentId}`
            );
            
            // Load chat details
            const response = await apiRequest(`/chat/${chatId}`);
            
            if (response.success) {
                const chat = response.data;
                
                // Update document info
                this.documentTitle.textContent = chat.document_name || 'Document';
                this.documentMeta.textContent = `${chat.message_count || 0} messages`;
                
                // Display messages
                if (chat.messages && chat.messages.length > 0) {
                    this.displayMessages(chat.messages);
                }
                
                // Enable input
                this.enableChatInput();
                
                showNotification('Chat session ready!', 'success');
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            console.error('Failed to load chat session:', error);
            showNotification('Failed to load chat session', 'error');
        }
    }
    
    displayMessages(messages) {
        // Clear existing messages (keep welcome message)
        const welcomeMessage = this.messagesContainer.querySelector('.message.ai');
        this.messagesContainer.innerHTML = '';
        
        if (welcomeMessage) {
            this.messagesContainer.appendChild(welcomeMessage);
        }
        
        // Add chat messages (skip system messages)
        messages.filter(msg => msg.role !== 'system').forEach(msg => {
            this.addMessageToUI(msg.role, msg.content, msg.sources);
        });
        
        this.scrollToBottom();
    }
    
    enableChatInput() {
        this.messageInput.disabled = false;
        this.messageInput.placeholder = "Ask about your document...";
        this.sendButton.disabled = false;
        
        // Enable action buttons
        this.viewPdfBtn.disabled = false;
        this.downloadBtn.disabled = false;
        this.clearChatBtn.disabled = false;
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isTyping || !this.currentChatId) {
            return;
        }
        
        // Add user message to UI
        this.addMessageToUI('user', message);
        this.messageInput.value = '';
        this.updateSendButton();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await apiRequest(`/chat/${this.currentChatId}/message`, {
                method: 'POST',
                body: JSON.stringify({ message })
            });
            
            this.hideTypingIndicator();
            
            if (response.success) {
                this.addMessageToUI('ai', response.data.response, response.data.sources);
                
                // Update message count in header
                this.documentMeta.textContent = `${response.data.message_count} messages`;
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Send message error:', error);
            this.addMessageToUI('ai', 'Sorry, I encountered an error. Please try again.', [], true);
        }
    }
    
    addMessageToUI(role, content, sources = [], isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatarIcon = role === 'user' ? 'person' : 'smart_toy';
        const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        // Create sources HTML
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="message-sources">
                    <strong>Sources:</strong>
                    ${sources.map(source => `
                        <div class="source-item">
                            <i class="material-icons">link</i>
                            <span>Source ${source.chunk_index + 1}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="material-icons">${avatarIcon}</i>
            </div>
            <div class="message-content ${isError ? 'error' : ''}">
                <div class="message-text">${content}</div>
                <div class="message-time">${timestamp}</div>
                ${sourcesHtml}
            </div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="material-icons">smart_toy</i>
            </div>
            <div class="typing-indicator">
                <span>Thinking</span>
                <div class="typing-dots">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    }
    
    sendSuggestion(question) {
        if (!this.currentChatId) {
            showNotification('Please select a document first', 'warning');
            return;
        }
        
        this.messageInput.value = question;
        this.updateSendButton();
        this.sendMessage();
    }
    
    updateSendButton() {
        this.sendButton.disabled = this.messageInput.value.trim().length === 0 || 
                                 this.isTyping || 
                                 !this.currentChatId;
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }
    
    highlightCurrentDocument() {
        const currentDoc = this.documentsList.querySelector(`[data-id="${this.currentDocumentId}"]`);
        if (currentDoc) {
            currentDoc.classList.add('selected');
        }
    }
    
    filterDocuments(query) {
        const documentItems = this.documentsList.querySelectorAll('.document-item');
        const lowerQuery = query.toLowerCase().trim();
        
        documentItems.forEach(item => {
            const filename = item.getAttribute('data-filename').toLowerCase();
            const isVisible = lowerQuery === '' || filename.includes(lowerQuery);
            item.style.display = isVisible ? 'flex' : 'none';
        });
    }
    
    setWelcomeTime() {
        const welcomeTimeElement = document.getElementById('welcomeTime');
        if (welcomeTimeElement) {
            welcomeTimeElement.textContent = 
                new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        }
    }
    
    // Action button handlers
    async clearChat() {
        if (!this.currentChatId) return;
        
        if (!confirm('Are you sure you want to clear this chat?')) {
            return;
        }
        
        try {
            const response = await apiRequest(`/chat/${this.currentChatId}/clear`, {
                method: 'POST'
            });
            
            if (response.success) {
                // Clear messages except welcome
                const welcomeMessage = this.messagesContainer.querySelector('.message.ai');
                this.messagesContainer.innerHTML = '';
                if (welcomeMessage) {
                    this.messagesContainer.appendChild(welcomeMessage);
                }
                
                showNotification('Chat cleared successfully', 'success');
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            console.error('Clear chat error:', error);
            showNotification(`Failed to clear chat: ${error.message}`, 'error');
        }
    }
    
    viewPdf() {
        showNotification('PDF viewer will appear here', 'info');
        // Actual implementation would go here
    }
    
    downloadPdf() {
        showNotification('PDF download will start here', 'info');
        // Actual implementation would go here
    }
}

// Initialize chat manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatManager = new ChatManager();
    window.chatManager.init();
});
