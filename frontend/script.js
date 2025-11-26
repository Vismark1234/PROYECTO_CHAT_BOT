// ===== DOM ELEMENTS =====
const chatButton = document.getElementById('chat-button');
const chatWindow = document.getElementById('chat-window');
const closeChat = document.getElementById('close-chat');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const quickReplies = document.querySelectorAll('.quick-reply-btn');
const notificationBadge = document.querySelector('.notification-badge');

// Image Modal Elements
const imageModal = document.getElementById('image-modal');
const modalImage = document.getElementById('modal-image');
const closeModal = document.getElementById('close-modal');
const prevImageBtn = document.getElementById('prev-image');
const nextImageBtn = document.getElementById('next-image');
const imageCounter = document.getElementById('image-counter');

// Image Modal State
let currentImages = [];
let currentImageIndex = 0;

function normalizeString(str) {
    return str
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/\s+/g, '');
}

function insertSectionImages(container, sections, usedImages) {
    const searchableNodes = Array.from(container.querySelectorAll('strong, p, li'));

    sections.forEach(section => {
        if (!section.images || !section.images.length) return;

        const sectionTitleNormalized = normalizeString(section.title || '');
        if (!sectionTitleNormalized) return;

        let targetNode = searchableNodes.find(node =>
            normalizeString(node.textContent || '').includes(sectionTitleNormalized)
        );

        const groupDiv = document.createElement('div');
        groupDiv.className = 'section-image-group';
        groupDiv.dataset.section = section.title;

        const label = document.createElement('div');
        label.className = 'section-image-label';
        label.textContent = `Imágenes ${section.title}`;
        groupDiv.appendChild(label);

        section.images.forEach(imageUrl => {
            if (!imageUrl || usedImages.has(imageUrl)) return;
            const imageDiv = document.createElement('div');
            imageDiv.className = 'message-image';
            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = `${section.title} - referencia visual`;
            img.loading = 'lazy';
            img.dataset.imageUrl = imageUrl;
            img.onerror = function () {
                this.style.display = 'none';
            };
            img.addEventListener('click', () => {
                openImageModal(section.images, section.images.indexOf(imageUrl));
            });
            imageDiv.appendChild(img);
            groupDiv.appendChild(imageDiv);
            usedImages.add(imageUrl);
        });

        if (groupDiv.childNodes.length <= 1) return;

        if (targetNode) {
            const parentBlock = targetNode.closest('p, li, div') || targetNode;
            parentBlock.parentNode.insertBefore(groupDiv, parentBlock.nextSibling);
        } else {
            container.appendChild(groupDiv);
        }
    });
}

// ===== STATE =====
let isChatOpen = false;

// ===== CONFIGURATION =====
const API_URL = '/api/chat';

// ===== UTILITY FUNCTIONS =====
function getCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

function scrollToBottom() {
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

function createMessageElement(text, isUser = false, images = [], sectionImages = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z" fill="currentColor"/>
        </svg>
    `;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textP = document.createElement('div'); // Changed to div to contain HTML
    // Parse markdown if marked is available, otherwise use plain text
    if (typeof marked !== 'undefined') {
        textP.innerHTML = marked.parse(text);
    } else {
        textP.textContent = text;
    }

    const usedImages = new Set();

    if (!isUser && sectionImages && sectionImages.length > 0) {
        insertSectionImages(textP, sectionImages, usedImages);
    }

    // Agregar imágenes si están disponibles (solo para mensajes del bot)
    if (!isUser && images && images.length > 0) {
        images.forEach((imageUrl, index) => {
            if (imageUrl && imageUrl.trim() && !usedImages.has(imageUrl)) {
                const imageDiv = document.createElement('div');
                imageDiv.className = 'message-image';
                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = 'Documento requerido';
                img.loading = 'lazy';
                img.dataset.imageIndex = index;
                img.dataset.imageUrl = imageUrl;
                img.onerror = function () {
                    // Si la imagen falla al cargar, ocultarla
                    this.style.display = 'none';
                };
                img.addEventListener('click', () => {
                    openImageModal(images, images.indexOf(imageUrl));
                });
                imageDiv.appendChild(img);
                contentDiv.appendChild(imageDiv);
                usedImages.add(imageUrl);
            }
        });
    }

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = getCurrentTime();

    contentDiv.appendChild(textP);
    contentDiv.appendChild(timeSpan);

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    return messageDiv;
}

function createTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.id = 'typing-indicator';

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z" fill="currentColor"/>
        </svg>
    `;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    contentDiv.appendChild(typingDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    return messageDiv;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// ===== CHAT FUNCTIONALITY =====
function toggleChat() {
    isChatOpen = !isChatOpen;
    chatWindow.classList.toggle('active');
    chatButton.classList.toggle('active');

    if (isChatOpen) {
        chatInput.focus();
        // Hide notification badge when chat is opened
        if (notificationBadge) {
            notificationBadge.style.display = 'none';
        }
    }
}

async function getBotResponse(userMessage) {
    try {
        // Get or create session ID
        let sessionId = localStorage.getItem('chatbot_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chatbot_session_id', sessionId);
        }

        // Call backend API
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }

        const data = await response.json();

        if (data.success) {
            return {
                message: data.message,
                images: data.images || [],
                sectionImages: data.section_images || []
            };
        } else {
            throw new Error(data.error || 'Error desconocido');
        }

    } catch (error) {
        console.error('Error calling backend:', error);

        // Mensajes de error más específicos
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            return '⚠️ No se pudo conectar con el servidor. Por favor, verifica que el backend esté ejecutándose en http://localhost:5000';
        }

        // Fallback response if backend is not available
        return '⚠️ Lo siento, el servidor no está disponible en este momento. Por favor, asegúrate de que el backend esté ejecutándose (python app.py) o intenta más tarde.';
    }
}

async function sendMessage(text) {
    if (!text.trim()) return;

    // Add user message
    const userMessage = createMessageElement(text, true);
    chatMessages.appendChild(userMessage);
    scrollToBottom();

    // Clear input
    chatInput.value = '';

    // Show typing indicator
    setTimeout(async () => {
        const typingIndicator = createTypingIndicator();
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();

        // Get bot response from backend
        try {
            const botResponse = await getBotResponse(text);
            removeTypingIndicator();
            const botMessage = createMessageElement(
                botResponse.message || botResponse,
                false,
                botResponse.images || [],
                botResponse.sectionImages || []
            );
            chatMessages.appendChild(botMessage);
            scrollToBottom();
        } catch (error) {
            removeTypingIndicator();
            const errorMessage = createMessageElement('Lo siento, ocurrió un error. Por favor, intenta de nuevo.');
            chatMessages.appendChild(errorMessage);
            scrollToBottom();
        }
    }, 500);
}

// ===== EVENT LISTENERS =====
chatButton.addEventListener('click', toggleChat);
closeChat.addEventListener('click', toggleChat);

sendButton.addEventListener('click', () => {
    sendMessage(chatInput.value);
});

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage(chatInput.value);
    }
});

// Quick replies
quickReplies.forEach(button => {
    button.addEventListener('click', () => {
        const text = button.textContent.trim();
        sendMessage(text);
    });
});

// Welcome links - hacer que actúen como prompts
function initWelcomeLinks() {
    const welcomeLinks = document.querySelectorAll('.welcome-link');
    welcomeLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const prompt = link.getAttribute('data-prompt');
            if (prompt) {
                sendMessage(prompt);
            }
        });
    });
}

// Inicializar enlaces de bienvenida cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWelcomeLinks);
} else {
    // DOM ya está listo
    initWelcomeLinks();
}

// ===== HEALTH CHECK =====
async function checkBackendHealth() {
    try {
        const response = await fetch('http://localhost:5000/api/health');
        const data = await response.json();

        if (data.status === 'ok' && data.chatbot_ready) {
            console.log('✅ Backend conectado y listo');
            console.log('🤖 Modelo:', data.ai_model);
            return true;
        } else {
            console.warn('⚠️ Backend no está completamente listo');
            return false;
        }
    } catch (error) {
        console.error('❌ No se pudo conectar con el backend:', error);
        console.warn('💡 Asegúrate de que el servidor esté ejecutándose: python backend/app.py');
        return false;
    }
}

// ===== IMAGE MODAL FUNCTIONS =====
function openImageModal(images, startIndex = 0) {
    if (!images || images.length === 0) return;

    currentImages = images.filter(url => url && url.trim());
    currentImageIndex = startIndex;

    if (currentImages.length === 0) return;

    updateModalImage();
    imageModal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevenir scroll del body
}

function closeImageModal() {
    imageModal.classList.remove('active');
    document.body.style.overflow = ''; // Restaurar scroll
    currentImages = [];
    currentImageIndex = 0;
}

function updateModalImage() {
    if (currentImages.length === 0) return;

    if (currentImageIndex < 0) currentImageIndex = currentImages.length - 1;
    if (currentImageIndex >= currentImages.length) currentImageIndex = 0;

    modalImage.src = currentImages[currentImageIndex];
    imageCounter.textContent = `${currentImageIndex + 1} / ${currentImages.length}`;

    // Mostrar/ocultar botones de navegación
    prevImageBtn.style.display = currentImages.length > 1 ? 'flex' : 'none';
    nextImageBtn.style.display = currentImages.length > 1 ? 'flex' : 'none';
    imageCounter.style.display = currentImages.length > 1 ? 'block' : 'none';
}

function nextImage() {
    currentImageIndex++;
    updateModalImage();
}

function prevImage() {
    currentImageIndex--;
    updateModalImage();
}

// Event listeners para el modal
if (closeModal) {
    closeModal.addEventListener('click', closeImageModal);
}

if (prevImageBtn) {
    prevImageBtn.addEventListener('click', prevImage);
}

if (nextImageBtn) {
    nextImageBtn.addEventListener('click', nextImage);
}

// Cerrar modal al hacer click en el overlay
if (imageModal) {
    imageModal.addEventListener('click', (e) => {
        if (e.target === imageModal || e.target.classList.contains('image-modal-overlay')) {
            closeImageModal();
        }
    });
}

// Cerrar modal con tecla ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && imageModal.classList.contains('active')) {
        closeImageModal();
    } else if (e.key === 'ArrowLeft' && imageModal.classList.contains('active')) {
        prevImage();
    } else if (e.key === 'ArrowRight' && imageModal.classList.contains('active')) {
        nextImage();
    }
});

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🤖 Chatbot BECATS initialized');
    console.log('📡 Backend API:', API_URL);

    // Verificar salud del backend
    await checkBackendHealth();

    // Optional: Show a welcome notification after a delay
    setTimeout(() => {
        if (!isChatOpen && notificationBadge) {
            notificationBadge.style.display = 'flex';
        }
    }, 3000);
});

// ===== IFRAME COMMUNICATION (Optional) =====
// You can add communication with the iframe if needed
window.addEventListener('message', (event) => {
    // Verify origin for security
    if (event.origin !== 'https://becats.umsa.bo') return;

    // Handle messages from iframe if needed
    console.log('Message from iframe:', event.data);
});
