/**
 * SAV.IN Enhanced Chat Controller - WITH REAL AI RESPONSES & DOCUMENT PREVIEW
 */

class ChatManager {
    constructor() {
        // State management
        this.currentChatId = null;
        this.selectedDocuments = new Set();
        this.chatSessions = new Map();
        this.isTyping = false;
        this.availableDocuments = [];
        this.currentDocumentContent = null;
        // Buffer for streaming thoughts
        this.thinkingLines = [];
        // Maximum number of thought lines to display before truncating
        this.thinkMaxLines = 4;
        
        // DOM Elements
        this.chatList = document.getElementById('chatList');
        this.createChatBtn = document.getElementById('createChatBtn');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendBtn');
        this.currentChatTitle = document.getElementById('currentChatTitle');
        this.currentChatMeta = document.getElementById('currentChatMeta');
        this.selectedDocsContainer = document.getElementById('selectedDocuments');
        this.documentList = document.getElementById('documentList');
        this.pdfPreview = document.getElementById('pdfPreview');
        
        // Modals
        this.modalOverlay = document.getElementById('modalOverlay');
        this.chatModal = document.getElementById('chatModal');
        this.chatNameInput = document.getElementById('chatNameInput');
        this.createChatConfirmBtn = document.getElementById('createChatConfirmBtn');
        
        // AI Response Templates - MORE VARIETY
        this.responseTemplates = [
            {
                trigger: ['what', 'explain', 'about'],
                response: (topic, docs) => `Based on my analysis of ${docs}, here's what I understand about ${topic}:\n\n**Key Points:**\n• This appears to be related to your document content\n• The information suggests multiple aspects to consider\n• There are important details that warrant further exploration\n\n**Context Analysis:**\nFrom the selected documents, I can see relevant information that directly addresses your question. The content provides comprehensive coverage of the topic you're asking about.`
            },
            {
                trigger: ['how', 'process', 'method'],
                response: (topic, docs) => `Here's my analysis of the process/methodology from ${docs}:\n\n**Step-by-Step Breakdown:**\n1. **Initial Phase**: The document outlines the foundational approach\n2. **Implementation**: Key procedures and methodologies are detailed\n3. **Execution**: Practical applications and real-world examples\n4. **Results**: Expected outcomes and success metrics\n\n**Technical Details:**\nThe documentation provides specific guidance on implementation, with clear examples and best practices outlined throughout.`
            },
            {
                trigger: ['why', 'reason', 'because'],
                response: (topic, docs) => `Let me explain the reasoning based on ${docs}:\n\n**Primary Reasons:**\n• **Foundational Logic**: The underlying principles support this approach\n• **Evidence-Based**: Data and research back up these conclusions\n• **Practical Benefits**: Real-world advantages are clearly demonstrated\n\n**Supporting Analysis:**\nThe document provides compelling evidence through case studies, statistical analysis, and expert insights that justify this particular approach or conclusion.`
            },
            {
                trigger: ['compare', 'difference', 'versus', 'vs'],
                response: (topic, docs) => `Here's a comparative analysis from ${docs}:\n\n**Comparison Overview:**\n\n| Aspect | Option A | Option B |\n|--------|----------|----------|\n| Advantages | Multiple benefits outlined | Alternative strengths noted |\n| Considerations | Important factors to weigh | Different priorities highlighted |\n| Applications | Specific use cases detailed | Unique scenarios addressed |\n\n**Recommendation:**\nBased on the document analysis, the choice depends on your specific requirements and contextual factors as outlined in the source material.`
            },
            {
                trigger: ['python', 'code', 'programming', 'development'],
                response: (topic, docs) => `Based on the programming content in ${docs}, here's what I found:\n\n**Programming Insights:**\n\`\`\`python\n# Example concepts from the document\nkey_concepts = [\n    "Data analysis techniques",\n    "Implementation strategies", \n    "Best practices",\n    "Common patterns"\n]\n\`\`\`\n\n**Technical Analysis:**\n• **Methodology**: The document covers systematic approaches\n• **Implementation**: Practical code examples and patterns\n• **Best Practices**: Industry-standard recommendations\n• **Applications**: Real-world use cases and scenarios\n\n**Key Takeaways:**\nThe documentation provides comprehensive coverage of programming concepts with practical examples and implementation guidance.`
            },
            {
                trigger: ['data', 'analysis', 'statistics', 'numbers'],
                response: (topic, docs) => `Here's my data analysis from ${docs}:\n\n**Data Insights:**\n📊 **Statistical Overview:**\n• Sample sizes and methodologies are clearly documented\n• Analytical approaches are systematically outlined\n• Results interpretation is provided with context\n\n**Key Metrics:**\n- **Accuracy**: High confidence in presented data\n- **Relevance**: Directly applicable to your query\n- **Completeness**: Comprehensive coverage of the topic\n\n**Analytical Summary:**\nThe document presents well-structured data analysis with clear methodologies, reliable sources, and actionable insights for practical application.`
            }
        ];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadDocuments();
        this.loadChats();
        this.initializeFromURL();
        this.initializePdfPreview();
        console.log('ChatManager initialized with enhanced AI responses');
    }
    
    setupEventListeners() {
        // Create chat button
        this.createChatBtn?.addEventListener('click', () => this.showCreateChatModal());
        
        // Modal events
        this.createChatConfirmBtn?.addEventListener('click', () => this.createNewChat());
        this.modalOverlay?.addEventListener('click', (e) => {
            if (e.target === this.modalOverlay) {
                this.hideModal();
            }
        });
        
        // Chat name input
        this.chatNameInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.createNewChat();
            }
        });
        
        // Message input
        this.messageInput?.addEventListener('input', () => this.updateSendButton());
        this.messageInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button
        this.sendButton?.addEventListener('click', () => this.sendMessage());
        
        // Auto-save on page unload
        window.addEventListener('beforeunload', () => this.saveChatHistory());
        
        console.log('Event listeners setup complete');
    }
    
    initializePdfPreview() {
        if (!this.pdfPreview) {
            console.warn('PDF preview element not found - creating fallback');
            // Create fallback preview element if not found
            const pdfViewer = document.querySelector('.pdf-viewer .viewer-content');
            if (pdfViewer) {
                pdfViewer.innerHTML = '<div id="pdfPreview" class="pdf-content"></div>';
                this.pdfPreview = document.getElementById('pdfPreview');
            }
        }
        
        this.showDefaultPreview();
    }

    
    
    showDefaultPreview() {
        if (this.pdfPreview) {
            this.pdfPreview.innerHTML = `
                <div class="empty-state">
                    <i class="material-icons">description</i>
                    <h4>Document Preview</h4>
                    <p>Select documents and start chatting to see AI-highlighted sources appear here</p>
                    <small>The AI will automatically highlight relevant sections as you ask questions</small>
                </div>
            `;
        }
    }
    
    async loadDocuments() {
        console.log('Loading documents...');
        
        if (!this.documentList) {
            console.error('Document list element not found');
            return;
        }
        
        try {
            // Show loading state
            this.documentList.innerHTML = `
                <div class="loading-placeholder">
                    <div class="spinner"></div>
                    <p>Loading documents...</p>
                </div>
            `;
            
            const response = await apiRequest('/document/list');
            console.log('Documents API response:', response);
            
            if (response.success && response.data) {
                this.availableDocuments = response.data.filter(doc => doc.status === 'completed');
                console.log('Available documents:', this.availableDocuments);
                this.renderDocumentList();
            } else {
                throw new Error(response.message || 'No data received');
            }
            
        } catch (error) {
            console.error('Failed to load documents:', error);
            this.renderDocumentError('Failed to load documents: ' + error.message);
        }
    }

    async loadChats() {
        if (!this.chatList) return;

        this.chatList.innerHTML = `
            <div class="loading-placeholder">
                <div class="spinner"></div>
                <p>Loading chats...</p>
            </div>
        `;

        try {
            const response = await apiRequest('/chat/list');

            if (response.success && response.data) {
                this.chatSessions = new Map();
                response.data.forEach(chat => {
                    this.chatSessions.set(chat.id, {
                        id: chat.id,
                        title: chat.title,
                        messages: [],
                        selectedDocuments: new Set(),
                        created_at: chat.created_at,
                        last_activity: chat.last_activity
                    });
                });
                this.renderChatList();
            } else {
                throw new Error(response.message || 'No data received');
            }
        } catch (error) {
            console.error('Failed to load chats:', error);
            this.chatList.innerHTML = `
                <div class="empty-state">
                    <i class="material-icons">error</i>
                    <h4>Error loading chats</h4>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }
    
    renderDocumentList() {
        console.log('Rendering document list, count:', this.availableDocuments.length);
        
        if (!this.documentList) {
            console.error('Document list container not found');
            return;
        }
        
        if (!this.availableDocuments || this.availableDocuments.length === 0) {
            this.renderEmptyDocuments();
            return;
        }
        
        const documentsHtml = this.availableDocuments.map(doc => `
            <div class="document-item" data-id="${doc.id}" data-filename="${doc.filename}">
                <div class="document-checkbox">
                    <i class="material-icons" style="font-size: 16px;">check</i>
                </div>
                <div class="document-icon">
                    <i class="material-icons">picture_as_pdf</i>
                </div>
                <div class="document-details">
                    <h4>${doc.filename || 'Unknown Document'}</h4>
                    <p>${doc.file_size || 0} MB • ${doc.chunk_count || 0} chunks</p>
                </div>
            </div>
        `).join('');
        
        this.documentList.innerHTML = documentsHtml;
        console.log('Documents rendered successfully');
        
        // Add click handlers
        this.addDocumentClickHandlers();
    }
    
    addDocumentClickHandlers() {
        const documentItems = this.documentList.querySelectorAll('.document-item');
        console.log('Adding click handlers to', documentItems.length, 'documents');
        
        documentItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const docId = parseInt(item.getAttribute('data-id'));
                const filename = item.getAttribute('data-filename');
                console.log('Document clicked:', docId, filename);
                this.toggleDocumentSelection(docId, item);
            });
        });
    }
    
    async toggleDocumentSelection(docId, element) {
        console.log('Toggling document selection:', docId);
        
        if (this.selectedDocuments.has(docId)) {
            this.selectedDocuments.delete(docId);
            element.classList.remove('selected');
            console.log('Document deselected:', docId);
        } else {
            this.selectedDocuments.add(docId);
            element.classList.add('selected');
            console.log('Document selected:', docId);
            
            // Load document content for preview
            await this.loadDocumentContent(docId);
        }
        
        this.updateSelectedDocumentsDisplay();
        this.updateChatInputState();
        this.updateDocumentPreview();
    }
    
    async loadDocumentContent(docId) {
        try {
            console.log('Loading content for document:', docId);
            const response = await apiRequest(`/document/${docId}/content`);

            if (response.success && response.data.content) {
                this.currentDocumentContent = response.data.content;
                console.log('Document content loaded, length:', this.currentDocumentContent.length);
            } else {
                console.warn('No content available for document:', docId);
                showNotification('Document preview not available', 'warning');
            }
        } catch (error) {
            console.error('Failed to load document content:', error);
            showNotification('Failed to load preview', 'error');
        }
    }
    
    updateDocumentPreview() {
        if (!this.pdfPreview) return;
        
        if (this.selectedDocuments.size === 0) {
            this.showDefaultPreview();
            return;
        }

        if (!this.currentDocumentContent) {
            this.pdfPreview.innerHTML = `
                <div class="document-preview">
                    <p>No preview available. The document might still be processing.</p>
                </div>
            `;
            return;
        }
        
        // Display document content with proper formatting
        const selectedDocs = this.availableDocuments.filter(doc => 
            this.selectedDocuments.has(doc.id)
        );
        
        const docNames = selectedDocs.map(doc => doc.filename).join(', ');
        
        this.pdfPreview.innerHTML = `
            <div class="document-preview">
                <div class="preview-header">
                    <h3>📄 ${docNames}</h3>
                    <p>Document content will be highlighted as AI responds to your questions</p>
                </div>
                <div class="document-content">
                    ${this.formatDocumentContent(this.currentDocumentContent)}
                </div>
            </div>
        `;
    }
    
    formatDocumentContent(content) {
        if (!content) return '<p>No content available</p>';
        
        // Split content by pages and format
        return content
            .split(/---\s*Page\s+\d+\s*---/)
            .map((pageContent, index) => {
                if (!pageContent.trim()) return '';
                
                const formattedPage = pageContent.trim()
                    .split('\n\n')
                    .map(paragraph => {
                        if (!paragraph.trim()) return '';
                        return `<p>${paragraph.trim()}</p>`;
                    })
                    .join('');
                
                return index === 0 ? formattedPage : `
                    <div class="page-separator">📄 Page ${index}</div>
                    ${formattedPage}
                `;
            })
            .join('');
    }
    
    highlightSourceInPreview(sourceText) {
        if (!this.pdfPreview || !sourceText) return;

        const content = this.pdfPreview.innerHTML;
        // Remove any previous highlights
        this.pdfPreview.innerHTML = content.replace(/<span class="source-highlight">(.*?)<\/span>/gi, '$1');

        const escaped = this.escapeRegex(sourceText).replace(/\s+/g, '\\s+');
        const regex = new RegExp(`(${escaped})`, 'gi');
        const highlightedContent = this.pdfPreview.innerHTML.replace(regex, '<span class="source-highlight">$1</span>');

        this.pdfPreview.innerHTML = highlightedContent;
        
        // Scroll to first highlighted section
        setTimeout(() => {
            const highlighted = this.pdfPreview.querySelector('.source-highlight');
            if (highlighted) {
                highlighted.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    formatMessageText(text) {
        if (!text) return '';
        const lines = text.split('\n');
        let html = '';
        let inList = false;
        for (const raw of lines) {
            let line = raw.trim();
            if (/^[-*•]\s+/.test(line)) {
                if (!inList) { html += '<ul>'; inList = true; }
                line = line.replace(/^[-*•]\s+/, '');
                line = this.escapeHtml(line).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                html += `<li>${line}</li>`;
            } else if (line) {
                if (inList) { html += '</ul>'; inList = false; }
                line = this.escapeHtml(line).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                html += `<p>${line}</p>`;
            }
        }
        if (inList) html += '</ul>';
        return html;
    }
    
    updateSelectedDocumentsDisplay() {
        if (!this.selectedDocsContainer) return;
        
        const selectedDocs = this.availableDocuments.filter(doc => 
            this.selectedDocuments.has(doc.id)
        );
        
        console.log('Selected documents:', selectedDocs.length);
        
        this.selectedDocsContainer.innerHTML = selectedDocs.map(doc => `
            <div class="selected-doc-chip">
                <i class="material-icons">description</i>
                ${doc.filename}
            </div>
        `).join('');
        
        // Update meta information
        if (this.currentChatMeta) {
            this.currentChatMeta.innerHTML = `
                <span>${selectedDocs.length} document${selectedDocs.length !== 1 ? 's' : ''} selected</span>
                <span>•</span>
                <span>Ready to chat</span>
            `;
        }
    }
    
    renderEmptyDocuments() {
        console.log('Rendering empty documents state');
        this.documentList.innerHTML = `
            <div class="empty-state">
                <i class="material-icons">description</i>
                <h4>No documents available</h4>
                <p>Upload PDF documents first to start chatting</p>
                <small>Go to the Upload page to add documents</small>
            </div>
        `;
    }
    
    renderDocumentError(message) {
        console.error('Rendering document error:', message);
        this.documentList.innerHTML = `
            <div class="empty-state">
                <i class="material-icons">error</i>
                <h4>Error loading documents</h4>
                <p>${message}</p>
                <small>Please try refreshing the page</small>
            </div>
        `;
    }
    
    updateChatInputState() {
        const hasDocuments = this.selectedDocuments.size > 0;
        const hasActiveChat = this.currentChatId !== null;
        
        if (this.messageInput) {
            this.messageInput.disabled = !(hasDocuments && hasActiveChat) || this.isTyping;
            this.messageInput.placeholder = hasActiveChat
                ? (hasDocuments ? "Ask about your documents..." : "Select documents first...")
                : "Create or select a chat first...";
        }
        
        this.updateSendButton();
    }
    
    updateSendButton() {
        if (!this.sendButton || !this.messageInput) return;
        
        const hasText = this.messageInput.value.trim().length > 0;
        const canSend = hasText && this.selectedDocuments.size > 0 && this.currentChatId && !this.isTyping;
        
        this.sendButton.disabled = !canSend;
    }
    
    showCreateChatModal() {
        console.log('Showing create chat modal');
        if (this.modalOverlay && this.chatNameInput) {
            this.modalOverlay.style.display = 'flex';
            this.chatNameInput.value = `Chat ${this.chatSessions.size + 1}`;
            this.chatNameInput.focus();
            this.chatNameInput.select();
        }
    }
    
    hideModal() {
        if (this.modalOverlay) {
            this.modalOverlay.style.display = 'none';
        }
    }
    
    async createNewChat() {
        const chatName = this.chatNameInput?.value.trim();
        if (!chatName) return;
        
        console.log('Creating new chat:', chatName);
        
        try {
            const response = await apiRequest('/chat/create', {
                method: 'POST',
                body: JSON.stringify({
                    title: chatName,
                    document_ids: Array.from(this.selectedDocuments)
                })
            });

            if (!response.success) throw new Error(response.message);

            const chatData = response.data;
            const newChat = {
                id: chatData.id,
                title: chatData.title,
                messages: [],
                selectedDocuments: new Set(chatData.selected_documents || []),
                created_at: chatData.created_at,
                last_activity: chatData.last_activity
            };

            this.chatSessions.set(newChat.id, newChat);
            this.renderChatList();
            await this.selectChat(newChat.id);
            this.hideModal();

            showNotification(`Chat "${chatName}" created successfully!`, 'success');
            console.log('Chat created successfully:', newChat.id);
            
        } catch (error) {
            console.error('Failed to create chat:', error);
            showNotification('Failed to create chat', 'error');
        }
    }

    
    
    renderChatList() {
        if (!this.chatList) return;
        
        const chats = Array.from(this.chatSessions.values())
            .sort((a, b) => new Date(b.last_activity) - new Date(a.last_activity));
        
        console.log('Rendering chat list, count:', chats.length);
        
        if (chats.length === 0) {
            this.chatList.innerHTML = `
                <div class="empty-state">
                    <i class="material-icons">chat</i>
                    <h4>No chats yet</h4>
                    <p>Create your first chat to get started</p>
                </div>
            `;
            return;
        }
        
        this.chatList.innerHTML = chats.map(chat => `
            <div class="chat-item ${chat.id === this.currentChatId ? 'active' : ''}" 
                 data-id="${chat.id}">
                <div class="chat-icon">
                    <i class="material-icons">chat</i>
                </div>
                <div class="chat-details">
                    <div class="chat-title">${chat.title}</div>
                    <div class="chat-meta">
                        <span>${chat.messages.length} messages</span>
                        <span>•</span>
                        <span>${chat.selectedDocuments?.size || 0} docs</span>
                    </div>
                </div>
                <div class="chat-actions">
                    <button class="chat-action-btn" onclick="chatManager.deleteChat(${chat.id})" title="Delete Chat">
                        <i class="material-icons" style="font-size: 16px;">delete</i>
                    </button>
                </div>
            </div>
        `).join('');
        
        // Add click handlers
        this.chatList.querySelectorAll('.chat-item').forEach(item => {
            item.addEventListener('click', async (e) => {
                if (!e.target.closest('.chat-actions')) {
                    const chatId = parseInt(item.getAttribute('data-id'));
                    await this.selectChat(chatId);
                }
            });
        });
    }
    
    async selectChat(chatId) {
        console.log('Selecting chat:', chatId);

        let chat = this.chatSessions.get(chatId);
        if (!chat) {
            console.error('Chat not found:', chatId);
            return;
        }

        // Fetch chat details if messages not loaded yet
        if (!chat.messages || chat.messages.length === 0) {
            try {
                const response = await apiRequest(`/chat/${chatId}`);
                if (response.success && response.data) {
                    chat.messages = response.data.messages || [];
                }
            } catch (error) {
                console.error('Failed to fetch chat details:', error);
            }
        }

        this.currentChatId = chatId;
        
        // Update current chat display
        if (this.currentChatTitle) {
            this.currentChatTitle.textContent = chat.title;
        }
        
        // Restore selected documents
        this.selectedDocuments = new Set(chat.selectedDocuments || []);
        this.updateSelectedDocumentsInUI();
        this.updateSelectedDocumentsDisplay();
        
        // Display messages
        this.displayMessages(chat.messages || []);
        
        // Update URL
        window.history.replaceState({}, '', `/chat?chat_id=${chatId}`);
        
        // Update UI state
        this.renderChatList();
        this.updateChatInputState();
        this.updateDocumentPreview();
        
        // Update last activity
        chat.last_activity = new Date().toISOString();
        this.saveChatHistory();
        
        console.log('Chat selected successfully:', chatId);
    }
    
    updateSelectedDocumentsInUI() {
        // Update document list UI to show selections
        if (this.documentList) {
            this.documentList.querySelectorAll('.document-item').forEach(item => {
                const docId = parseInt(item.getAttribute('data-id'));
                if (this.selectedDocuments.has(docId)) {
                    item.classList.add('selected');
                } else {
                    item.classList.remove('selected');
                }
            });
        }
    }
    
    displayMessages(messages) {
        if (!this.messagesContainer) return;
        
        // Show placeholder if no messages
        if (!messages || messages.length === 0) {
            this.messagesContainer.innerHTML = `
                <div class="chat-placeholder">
                    <i class="material-icons">smart_toy</i>
                    <h3>Ready to Chat!</h3>
                    <p>Select documents and start asking questions about your PDFs using our local Sav.in AI models.</p>
                </div>
            `;
            return;
        }
        
        // Render messages
        this.messagesContainer.innerHTML = messages.map(msg => this.createMessageHTML(msg)).join('');
        this.scrollToBottom();
    }
    
    createMessageHTML(message) {

        const sourcesHTML = message.sources && message.sources.length > 0 ? `
            <div class="message-sources">
                <strong>Sources:</strong>
                ${message.sources.map((source, index) => `
                    <div class="source-item" onclick="chatManager.highlightSourceInPreview('${source.content}')">
                        <i class="material-icons">link</i>
                        <span>Source ${index + 1}</span>
                    </div>
                `).join('')}
            </div>
        ` : '';

        const formatted = this.formatMessageText(message.content);

        return `
            <div class="message ${message.role}">
                <div class="message-avatar">
                    <i class="material-icons">${message.role === 'user' ? 'person' : 'smart_toy'}</i>
                </div>
                <div class="message-content">
                    <div class="message-text">${formatted}</div>

                    ${sourcesHTML}
                </div>
            </div>
        `;
    }

    
    
    async sendMessage() {
        const messageText = this.messageInput?.value.trim();
        if (!messageText || !this.currentChatId || this.selectedDocuments.size === 0) {
            console.log('Cannot send message - missing requirements');
            return;
        }
        
        console.log('Sending message:', messageText);
        
        const chat = this.chatSessions.get(this.currentChatId);
        if (!chat) return;
        
        // Add user message
        const userMessage = {
            role: 'user',
            content: messageText,
            timestamp: new Date().toISOString()
        };
        
        chat.messages.push(userMessage);
        chat.selectedDocuments = new Set(this.selectedDocuments);
        this.displayMessages(chat.messages);
        // Show the dynamic thinking bubble
        this.showThinkingMessage();

        // Clear input and update UI state
        this.messageInput.value = '';
        this.updateSendButton();

        this.isTyping = true;
        this.updateChatInputState();

        try {
            // Attempt to stream the AI response line-by-line. If streaming fails,
            // fall back to the non-streaming implementation.
            await this.fetchStreamedAIResponse(chat, messageText);
        } catch (error) {
            console.error('Streaming failed, falling back to regular response:', error);
            try {
                await this.fetchLiveAIResponse(chat, messageText);
            } catch (error2) {
                console.error('Send message error:', error2);
                const errorMessage = {
                    role: 'ai',
                    content: 'Sorry, I encountered an error processing your request. Please try again.',
                    timestamp: new Date().toISOString(),
                    isError: true
                };
                chat.messages.push(errorMessage);
                this.displayMessages(chat.messages);
            }
        } finally {
            // Collapse and remove the thinking message once the full reply has been processed
            this.removeThinkingMessage();
            this.isTyping = false;
            this.updateChatInputState();
            chat.last_activity = new Date().toISOString();
            this.saveChatHistory();
        }
    }

    async fetchLiveAIResponse(chat, userMessage) {
        try{
            const response = await apiRequest(
                `/chat/${this.currentChatId}/message`,
                {
                    method : 'POST',
                    body : JSON.stringify({
                        message: userMessage,
                        document_ids: Array.from(this.selectedDocuments)
                    })
                }
            );
            if(!response.success)throw new Error(response.message);
            let {response : aiText, sources} = response.data;

            // Extract <think> sections from the response. These represent the
            // model's thought process and should be displayed in the thinking
            // bubble before showing the final answer.
            const thinkRegex = /<think>([\s\S]*?)<\/think>/gi;
            const thoughtLines = [];
            let match;
            while ((match = thinkRegex.exec(aiText)) !== null) {
                match[1].split(/\n+/).forEach(line => {
                    const trimmed = line.trim();
                    if (trimmed) thoughtLines.push(trimmed);
                });
            }

            // Remove <think> sections from the final answer text
            aiText = aiText.replace(thinkRegex, '').trim();

            // Display extracted thoughts sequentially in the thinking message
            for (const line of thoughtLines) {
                this.appendThinkingLine(line);
                // Small delay so the UI updates progressively
                await new Promise(r => setTimeout(r, 400));
            }

            this.removeThinkingMessage();
            chat.messages.push({
                role:'ai',
                content: aiText,
                timestamp: new Date().toISOString(),
                sources
            });
            await this.renderAiMessageStreaming(aiText, sources);
            this.displayMessages(chat.messages);
            if(sources?.length){
                this.highlightSourceInPreview(sources[0].content);
            }
        } catch (error) {
            console.error('Error fetching AI response:', error);
            this.removeThinkingMessage();
            chat.messages.push({
                role: 'ai',
                content: 'Sorry, I encountered an error processing your request. Please try again.',
                timestamp: new Date().toISOString(),
                isError: true
            })
            this.displayMessages(chat.messages);
        }
    }

    /**
     * Fetch the AI response using server-sent events (SSE) to stream
     * intermediate thoughts. The backend is expected to emit lines prefixed
     * with `data:` according to the SSE spec. Each payload may either be
     * a JSON object containing the final response or a raw text line
     * representing the assistant's thought process. When a JSON object
     * is received the final response is displayed and the method returns.
     * @param {Object} chat - Current chat session
     * @param {string} userMessage - The user message to send
     */
    async fetchStreamedAIResponse(chat, userMessage) {
        // Construct the POST request manually. Do not use apiRequest here
        const response = await fetch(`/chat/${this.currentChatId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: userMessage,
                document_ids: Array.from(this.selectedDocuments),
                stream: true
            })
        });

        // If response is not OK or the body is not readable, throw to trigger fallback
        if (!response.ok || !response.body) {
            throw new Error(`Bad response status: ${response.status}`);
        }

        const decoder = new TextDecoder();
        const reader = response.body.getReader();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            // Split the buffer into lines. SSE messages end with a newline.
            const lines = buffer.split('\n');
            // Keep the last partial line for the next iteration
            buffer = lines.pop();

            for (const raw of lines) {
                const line = raw.trim();
                if (!line.startsWith('data:')) continue;

                const payload = line.slice(5).trim();
                // End of stream indicator
                if (payload === '[DONE]') {
                    return;
                }

                // Attempt to parse the payload as JSON. If it fails, treat it as a thought line.
                let jsonData = null;
                try {
                    jsonData = JSON.parse(payload);
                } catch (err) {
                    jsonData = null;
                }

                if (jsonData && typeof jsonData === 'object' && !Array.isArray(jsonData)) {
                    // Final AI response with optional sources
                    const aiResponse = {
                        role: 'ai',
                        content: jsonData.response,
                        timestamp: new Date().toISOString(),
                        sources: jsonData.sources || []
                    };
                    chat.messages.push(aiResponse);
                    await this.renderAiMessageStreaming(jsonData.response, aiResponse.sources);
                    this.displayMessages(chat.messages);
                    // Highlight relevant source text if provided
                    const highlightText = jsonData.source_content || (aiResponse.sources && aiResponse.sources[0] && aiResponse.sources[0].content);
                    if (highlightText) {
                        this.highlightSourceInPreview(highlightText);
                    }
                    // After receiving the final response, we can finish
                    return;
                } else if (payload) {
                    // Treat the payload as a thought and append it
                    this.appendThinkingLine(payload);
                }
            }
        }
    }
    
    async generateDynamicAIResponse(chat, userMessage) {
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        const selectedDocs = this.availableDocuments.filter(doc => 
            this.selectedDocuments.has(doc.id)
        );
        
        const docNames = selectedDocs.map(doc => doc.filename).join(', ');
        const lowerMessage = userMessage.toLowerCase();
        
        // Find matching response template
        let responseTemplate = this.responseTemplates.find(template =>
            template.trigger.some(trigger => lowerMessage.includes(trigger))
        );
        
        // Default fallback template
        if (!responseTemplate) {
            responseTemplate = {
                response: (topic, docs) => `I've analyzed your question "${topic}" using the content from ${docs}.\n\n**Document Analysis:**\n• The selected documents contain relevant information about your query\n• Multiple perspectives and data points are available for consideration\n• Cross-referenced information provides comprehensive coverage\n\n**Key Insights:**\nBased on the document content, I can provide detailed information that directly addresses your specific question. The analysis reveals important patterns and connections within the material.\n\n**Contextual Summary:**\nThe documents offer valuable insights that align with your inquiry, presenting both theoretical foundations and practical applications relevant to your question.`
            };
        }
        
        // Generate response using template
        let aiResponseContent = responseTemplate.response(userMessage, docNames);
        
        // Add document-specific context if available
        if (this.currentDocumentContent) {
            const contentSample = this.currentDocumentContent.substring(0, 200) + '...';
            aiResponseContent += `\n\n**Document Context Preview:**\n*"${contentSample}"*\n\n*This is a sample from your selected document(s). The full analysis is based on the complete document content.*`;
        }
        
        // Create AI response with sources
        const aiResponse = {
            role: 'ai',
            content: aiResponseContent,
            timestamp: new Date().toISOString(),
            sources: selectedDocs.map((doc, index) => ({
                chunk_index: index,
                chunk_id: `${doc.id}_${index}`,
                content: this.currentDocumentContent ? 
                    this.currentDocumentContent.substring(index * 100, (index + 1) * 100) : 
                    `Content sample from ${doc.filename}`,
                filename: doc.filename
            }))
        };
        
        chat.messages.push(aiResponse);
        this.displayMessages(chat.messages);
        
        // Highlight sources in preview if available
        if (aiResponse.sources && aiResponse.sources.length > 0 && this.currentDocumentContent) {
            setTimeout(() => {
                this.highlightSourceInPreview(aiResponse.sources[0].content);
            }, 500);
        }
    }
    
    async deleteChat(chatId) {
        if (!confirm('Are you sure you want to delete this chat?')) return;

        console.log('Deleting chat:', chatId);

        try {
            const response = await apiRequest(`/chat/${chatId}`, {
                method: 'DELETE'
            });

            if (!response.success) {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('Failed to delete chat:', error);
            showNotification('Failed to delete chat', 'error');
            return;
        }

        this.chatSessions.delete(chatId);

        if (this.currentChatId === chatId) {
            this.currentChatId = null;
            this.selectedDocuments.clear();
            this.displayMessages([]);
            this.updateSelectedDocumentsDisplay();
            this.updateChatInputState();
            this.showDefaultPreview();
        }

        this.renderChatList();
        this.saveChatHistory();
        showNotification('Chat deleted successfully', 'success');
    }
    
    saveChatHistory() {
        try {
            const chatData = {
                sessions: Array.from(this.chatSessions.entries()).map(([id, chat]) => [
                    id, 
                    {
                        ...chat,
                        selectedDocuments: Array.from(chat.selectedDocuments || [])
                    }
                ]),
                currentChatId: this.currentChatId,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('savin_chat_history', JSON.stringify(chatData));
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
    }
    
    async loadChatHistory() {
        try {
            const saved = localStorage.getItem('savin_chat_history');
            if (saved) {
                const data = JSON.parse(saved);
                
                this.chatSessions = new Map(data.sessions || []);
                
                // Convert array back to Set
                this.chatSessions.forEach(chat => {
                    chat.selectedDocuments = new Set(chat.selectedDocuments || []);
                });
                
                this.renderChatList();
                
                if (data.currentChatId && this.chatSessions.has(data.currentChatId)) {
                    await this.selectChat(data.currentChatId);
                }
                
                console.log('Chat history loaded successfully');
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }
    
    async initializeFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const chatId = urlParams.get('chat_id');

        if (chatId) {
            const id = parseInt(chatId);
            if (this.chatSessions.has(id)) {
                await this.selectChat(id);
            }
        }
    }

    showThinkingMessage() {
        // Display a thinking message bubble for streaming thoughts. The bubble will
        // show up to thinkMaxLines of text and scroll automatically as new lines
        // arrive. If a thinking message already exists, do nothing.
        if (!this.messagesContainer || document.getElementById('thinkingMessage')) return;

        // Reset buffer
        this.thinkingLines = [];

        // Construct the thinking message. We reuse the existing styling for
        // `.message.thinking` to preserve the starry background and animation.
        const html = `
            <div class="message ai thinking" id="thinkingMessage">
                <div class="message-avatar">
                    <i class="material-icons">smart_toy</i>
                </div>
                <div class="message-content">
                    <div class="message-text" id="thinkingContent">
                        Thinking
                    </div>
                </div>
            </div>`;

        this.messagesContainer.insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
    }


    removeThinkingMessage() {
        const el = document.getElementById('thinkingMessage');
        if (!el) return;
        // Remove the thinking message immediately. We do not animate here because
        // the message-text area handles its own scroll and does not require
        // height transitions.
        el.remove();
        // Clear stored thought lines
        this.thinkingLines = [];
    }

    /**
     * Append a single thought line emitted by the backend and animate the thinking
     * bubble to reveal up to this.thinkMaxLines lines. Excess lines will be
     * truncated from the beginning of the buffer.
     *
     * @param {string} line - The line of thought to display
     */
    appendThinkingLine(line) {
        if (!line) return;
        const container = document.getElementById('thinkingContent');
        if (!container) return;

        // Trim whitespace and push to buffer
        this.thinkingLines.push(line.trim());
        if (this.thinkingLines.length > this.thinkMaxLines) {
            // Keep only the last N lines
            this.thinkingLines = this.thinkingLines.slice(-this.thinkMaxLines);
        }

        // Update the displayed text. Use newline characters; CSS will handle the
        // wrapping within the message-text container.
        container.textContent = this.thinkingLines.join('\n');

        // Scroll to the bottom of the thinking container to show the latest thought
        // If using message-text, it has overflow-y:auto defined and will scroll
        container.parentElement?.scrollTo({ top: container.parentElement.scrollHeight, behavior: 'smooth' });
    }

    async renderAiMessageStreaming(text, sources) {
        if (!this.messagesContainer) return;
        const id = 'ai_' + Date.now();
        const sourcesHTML = sources && sources.length > 0 ? `
            <div class="message-sources">
                <strong>Sources:</strong>
                ${sources.map((s, i) => `
                    <div class="source-item" onclick="chatManager.highlightSourceInPreview('${s.content}')">
                        <i class="material-icons">link</i>
                        <span>Source ${i + 1}</span>
                    </div>
                `).join('')}
            </div>
        ` : '';

        const wrapper = `
            <div class="message ai">
                <div class="message-avatar"><i class="material-icons">smart_toy</i></div>
                <div class="message-content">
                    <div class="message-text" id="${id}"></div>
                    ${sourcesHTML}
                </div>
            </div>`;

        this.messagesContainer.insertAdjacentHTML('beforeend', wrapper);
        const el = document.getElementById(id);
        if (!el) return;
        let idx = 0;
        while (idx <= text.length) {
            el.innerHTML = this.formatMessageText(text.slice(0, idx));
            this.scrollToBottom();
            await new Promise(r => setTimeout(r, 20));
            idx++;
        }
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            setTimeout(() => {
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }, 100);
        }
    }
}

// Initialize chat manager
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing ChatManager with enhanced features...');
    window.chatManager = new ChatManager();
});
