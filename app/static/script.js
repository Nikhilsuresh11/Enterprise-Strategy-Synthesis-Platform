/**
 * Stratagem AI - Frontend Logic
 */

const state = {
    step: 'initial', // initial, clarification, processing, completed
    jobId: null,
    company: '',
    industry: '',
    question: '',
    clarificationQuestion: '',
    clarificationAnswer: ''
};

// UI Elements
const welcomeScreen = document.getElementById('welcome-screen');
const messagesContainer = document.getElementById('messages-container');
const initialInputs = document.getElementById('initial-inputs');
const clarificationInputs = document.getElementById('clarification-inputs');
const analysisForm = document.getElementById('analysis-form');
const submitBtn = document.getElementById('submit-btn');
const loadingOverlay = document.getElementById('loading-overlay');
const progressBar = document.getElementById('progress-bar');
const loadingStatus = document.getElementById('loading-status');
const loadingDetail = document.getElementById('loading-detail');
const chatViewport = document.getElementById('chat-viewport');

// Helper: Add message to chat
function addMessage(role, content, isHtml = false) {
    welcomeScreen.classList.add('hidden');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatarIcon = role === 'user' ? 'user' : 'bot';
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = `<i data-lucide="${role === 'user' ? 'user' : 'sparkles'}"></i>`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    if (isHtml) {
        contentDiv.innerHTML = content;
    } else {
        contentDiv.textContent = content;
    }

    if (role === 'ai') {
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
    } else {
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(avatar);
    }

    messagesContainer.appendChild(messageDiv);
    lucide.createIcons();

    // Scroll to bottom
    chatViewport.scrollTo({
        top: chatViewport.scrollHeight,
        behavior: 'smooth'
    });
}

// Handle Form Submission
analysisForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (state.step === 'initial') {
        await handleInitialStep();
    } else if (state.step === 'clarification') {
        await handleClarificationStep();
    }
});

async function handleInitialStep() {
    state.company = document.getElementById('company_name').value;
    state.industry = document.getElementById('industry').value;
    state.question = document.getElementById('strategic_question').value;

    addMessage('user', state.question);

    // Show "thinking" state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner-small"></div>';

    try {
        const response = await fetch('/api/v1/clarify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: state.company,
                industry: state.industry,
                strategic_question: state.question
            })
        });

        const data = await response.json();
        state.clarificationQuestion = data.question;

        addMessage('ai', state.clarificationQuestion);

        // Switch inputs
        initialInputs.classList.add('hidden');
        clarificationInputs.classList.remove('hidden');
        document.getElementById('clarification_answer').focus();

        state.step = 'clarification';
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="arrow-up"></i>';
        lucide.createIcons();

    } catch (error) {
        console.error('Error fetching clarification:', error);
        addMessage('ai', "I'm having trouble reaching my synthesis engine. Please try again.");
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="arrow-up"></i>';
        lucide.createIcons();
    }
}

async function handleClarificationStep() {
    state.clarificationAnswer = document.getElementById('clarification_answer').value;
    if (!state.clarificationAnswer) return;

    addMessage('user', state.clarificationAnswer);

    // Show loading overlay
    loadingOverlay.classList.remove('hidden');
    state.step = 'processing';

    try {
        const response = await fetch('/api/v1/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: state.company,
                industry: state.industry,
                strategic_question: state.question,
                additional_context: {
                    clarification_question: state.clarificationQuestion,
                    clarification_answer: state.clarificationAnswer
                }
            })
        });

        const data = await response.json();
        state.jobId = data.job_id;

        // Start polling
        pollStatus();

    } catch (error) {
        console.error('Error starting analysis:', error);
        loadingOverlay.classList.add('hidden');
        addMessage('ai', "Failed to start the analysis engine. Please refresh and try again.");
    }
}

async function pollStatus() {
    if (!state.jobId) return;

    try {
        const response = await fetch(`/api/v1/status/${state.jobId}`);
        const data = await response.json();

        progressBar.style.width = `${data.progress}%`;

        if (data.status === 'processing') {
            loadingStatus.textContent = `Synthesizing Strategy... ${data.progress}%`;
            if (data.progress < 30) {
                loadingDetail.textContent = 'Agent 1: Mining deep markets and financial reports...';
            } else if (data.progress < 60) {
                loadingDetail.textContent = 'Agent 2 & 3: Mapping competitive landscape and regulatory hurdles...';
            } else {
                loadingDetail.textContent = 'Agent 4: Finalizing strategic synthesis and generating deck...';
            }

            setTimeout(pollStatus, 3000);
        } else if (data.status === 'completed') {
            showResults(data);
        } else if (data.status === 'failed') {
            loadingOverlay.classList.add('hidden');
            addMessage('ai', `Analysis failed: ${data.error_message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error polling status:', error);
        setTimeout(pollStatus, 5000);
    }
}

function showResults(data) {
    loadingOverlay.classList.add('hidden');
    state.step = 'completed';

    const resultHtml = `
        <h3>Strategic Synthesis Complete</h3>
        <p>I have analyzed <strong>${state.company}</strong> in the <strong>${state.industry}</strong> sector regarding your question. The agents have synthesized a comprehensive strategy based on current market trends, financial stability, and regulatory environment.</p>
        
        <div class="download-group">
            <button class="download-btn" onclick="downloadFile('pdf')">
                <i data-lucide="file-text"></i> Download PDF
            </button>
            <button class="download-btn" onclick="downloadFile('pptx')">
                <i data-lucide="presentation"></i> Download PPTX
            </button>
            <button class="download-btn" onclick="downloadFile('json')">
                <i data-lucide="code"></i> Export JSON
            </button>
        </div>
    `;

    addMessage('ai', resultHtml, true);

    // Reset form for new chat hint
    analysisForm.reset();
    clarificationInputs.classList.add('hidden');
    initialInputs.classList.remove('hidden');
    state.step = 'initial';
}

function downloadFile(format) {
    if (!state.jobId) return;
    window.open(`/api/v1/download/${state.jobId}/${format}`, '_blank');
}

// Global exposure for onclick
window.downloadFile = downloadFile;
window.prefill = (co, ind, q) => {
    document.getElementById('company_name').value = co;
    document.getElementById('industry').value = ind;
    document.getElementById('strategic_question').value = q;
};
