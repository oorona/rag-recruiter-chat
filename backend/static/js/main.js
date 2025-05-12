// backend/static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    // Element References
    const candidateList = document.getElementById('candidate-list');
    const searchInput = document.getElementById('candidate-search-input');
    const markdownTitle = document.getElementById('markdown-title');
    const markdownContent = document.getElementById('markdown-content');
    const chatHistory = document.getElementById('chat-history');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const conversationListHistory = document.getElementById('conversation-list-history'); // Conversation list UL
    const loadingIndicator = document.getElementById('loading-indicator');
    const tokenStatsDisplay = document.getElementById('token-stats-display');

    // State Variables
    let candidates = []; // Stores {id, display_name}
    let currentCandidateId = null;
    let allConversations = {}; // Stores { candidateId: [messages] }
    let currentConversationHistory = []; // Reference to the active history in allConversations
    let abortController = null;

    // --- Initialization ---
    loadCandidates();
    renderConversationList(); // Initial render (will show empty message)

    // --- Event Listeners ---
    searchInput.addEventListener('input', handleSearch);
    candidateList.addEventListener('click', handleCandidateSelection); // For selecting new candidates
    conversationListHistory.addEventListener('click', handleConversationListClick); // For switching conversations
    chatForm.addEventListener('submit', handleChatSubmit);

    // --- Core Functions ---

    async function loadCandidates() {
        setCandidateListMessage("Loading candidates...");
        try {
            const response = await fetch('/api/candidates');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            candidates = await response.json();
            renderCandidateList(candidates); // Render main candidate list
             if (candidates.length === 0) {
                 setCandidateListMessage("No candidates found.", false, true);
            }
        } catch (error) {
            console.error('Error loading candidates:', error);
            setCandidateListMessage("Error loading candidates.", true);
            candidates = [];
            renderCandidateList(candidates);
        }
    }

    function renderCandidateList(candidatesToRender) {
        candidateList.innerHTML = '';
        if (candidatesToRender.length === 0) {
            if (candidates.length > 0) { setCandidateListMessage("No candidates match search.", false, true); }
            else if (!candidateList.querySelector('.loading')) { setCandidateListMessage("No candidates found.", false, true); }
            return;
        }
        candidatesToRender.forEach(candidate => {
            const li = document.createElement('li');
            li.textContent = candidate.display_name;
            li.dataset.candidateId = candidate.id;
            if (candidate.id === currentCandidateId) { li.classList.add('selected'); }
            candidateList.appendChild(li);
        });
    }

    function setCandidateListMessage(message, isError = false, isInfo = false) {
        candidateList.innerHTML = '';
        const li = document.createElement('li'); li.textContent = message;
        li.classList.add(isError ? 'error' : (isInfo ? 'no-results' : 'loading'));
        candidateList.appendChild(li);
    }

    function handleSearch(event) {
        const searchTerm = event.target.value.toLowerCase();
        const filteredCandidates = candidates.filter(c => c.display_name.toLowerCase().includes(searchTerm));
        renderCandidateList(filteredCandidates);
    }

    // --- Candidate/Conversation Switching Logic ---

    function handleCandidateSelection(event) {
        if (event.target.tagName === 'LI' && event.target.dataset.candidateId) {
            switchConversation(event.target.dataset.candidateId);
        }
    }

    function handleConversationListClick(event) {
        if (event.target.tagName === 'LI' && event.target.dataset.candidateId) {
            switchConversation(event.target.dataset.candidateId);
        }
    }

    function switchConversation(selectedCandidateId) {
         if (selectedCandidateId === currentCandidateId) return; // No change needed

         console.log(`Switching conversation to: ${selectedCandidateId}`);

         if (abortController) {
             abortController.abort();
             console.log("Chat request aborted due to conversation switch.");
         }

         // Save current history
         if (currentCandidateId && Array.isArray(currentConversationHistory)) {
              allConversations[currentCandidateId] = currentConversationHistory;
              console.log(`Saved history for ${currentCandidateId}`);
         }

         // Set new current candidate ID
         currentCandidateId = selectedCandidateId;

         // Load or initialize history
         if (allConversations[currentCandidateId]) {
             currentConversationHistory = allConversations[currentCandidateId];
             console.log(`Loaded history for ${currentCandidateId}`);
         } else {
             currentConversationHistory = [];
             allConversations[currentCandidateId] = currentConversationHistory;
             console.log(`Initialized new history for ${currentCandidateId}`);
         }

        // --- Update UI ---
        const selectedCandidate = candidates.find(c => c.id === currentCandidateId);
        // Use fallback name if candidate data isn't loaded (shouldn't happen often)
        const candidateName = selectedCandidate ? selectedCandidate.display_name : selectedCandidateId;

        updateSelectedCandidateUI(candidateList.querySelector(`li[data-candidate-id="${currentCandidateId}"]`));
        renderConversationList(); // Update conversation list (highlights)

        markdownTitle.textContent = `${candidateName} - Details`;
        renderChatHistory(currentConversationHistory); // Display correct chat history

        chatInput.value = '';
        chatInput.disabled = false;
        sendButton.disabled = false;
        hideLoading();
        clearTokenStats();

        // --- Load Markdown (with diagnostic logs) ---
        console.log(`Calling loadMarkdown with ID: ${currentCandidateId}`); // DIAGNOSTIC
        loadMarkdown(currentCandidateId);
    }

    function updateSelectedCandidateUI(selectedElement) {
        const previousSelected = candidateList.querySelector('li.selected');
        if (previousSelected) previousSelected.classList.remove('selected');
        if (selectedElement) selectedElement.classList.add('selected');
    }

    function renderConversationList() {
        conversationListHistory.innerHTML = ''; // Clear
        const conversationIds = Object.keys(allConversations);

        if (conversationIds.length === 0) {
             const li = document.createElement('li');
             li.textContent = "No conversations yet.";
             li.classList.add('loading');
             conversationListHistory.appendChild(li);
             return;
        }

        conversationIds.forEach(candidateId => {
             const candidate = candidates.find(c => c.id === candidateId);
             const displayName = candidate ? candidate.display_name : candidateId; // Fallback name

             const li = document.createElement('li');
             li.textContent = displayName;
             li.dataset.candidateId = candidateId;

             if (candidateId === currentCandidateId) {
                 li.classList.add('selected');
             }
             conversationListHistory.appendChild(li);
         });
    }


    async function loadMarkdown(candidateId) {
        markdownContent.innerHTML = '<p>Loading details...</p>';
        console.log(`loadMarkdown function received ID: ${candidateId}`); // DIAGNOSTIC
        if (!candidateId) { // DIAGNOSTIC Check
             console.error("loadMarkdown called with undefined candidateId!");
             markdownContent.innerHTML = `<p class="error-message">Error: No candidate selected.</p>`;
             return;
        }
        const fetchUrl = `/api/candidates/${candidateId}/markdown`;
        console.log(`Fetching markdown from: ${fetchUrl}`); // DIAGNOSTIC

        try {
            const response = await fetch(fetchUrl);
            if (!response.ok) {
                if (response.status === 404) throw new Error(`Details not found.`);
                else throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            markdownContent.innerHTML = marked.parse(data.markdown);
            console.log(`Successfully loaded markdown for ${candidateId}`); // DIAGNOSTIC
        } catch (error) {
            console.error(`Error loading markdown for ${candidateId}:`, error); // DIAGNOSTIC
            markdownContent.innerHTML = `<p class="error-message">Error loading details: ${error.message}</p>`;
        }
    }


    // --- Chat Interaction ---

    async function handleChatSubmit(event) {
        event.preventDefault();
        const userMessage = chatInput.value.trim();
        if (!userMessage || !currentCandidateId) return;

        appendMessage('user', userMessage); // Adds to UI and currentConversationHistory

        const historyToSend = currentConversationHistory.slice(0, -1);

        chatInput.value = ''; showLoading(); clearTokenStats();
        abortController = new AbortController(); const signal = abortController.signal;

        try {
            const response = await fetch('/api/chat', {
                 method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_id: currentCandidateId, message: userMessage, history: historyToSend
                }),
                signal: signal
            });

             if (signal.aborted) { console.log("Fetch aborted"); return; }

             if (!response.ok) {
                let errorText = `HTTP error! status: ${response.status}`;
                try { const errorData = await response.json(); errorText = errorData.description || errorText; }
                catch (e) { errorText = await response.text() || errorText; if (errorText.length > 150) errorText = errorText.substring(0, 150) + '...'; }
                 throw new Error(errorText);
             }

            const data = await response.json();
            if (data.reply !== undefined) {
                 appendMessage('assistant', data.reply); // Adds to UI and currentConversationHistory
                 updateTokenStats(data.usage);
            } else { throw new Error("API success but no reply."); }
        } catch (error) {
             if (error.name === 'AbortError') { console.log('Chat aborted.'); }
             else {
                 console.error('Chat Error:', error);
                 appendMessage('system', `Error: ${error.message}`, true);
                 if (currentConversationHistory.length > 0 && currentConversationHistory[currentConversationHistory.length - 1].role === 'user') {
                     currentConversationHistory.pop(); // Rollback state
                 }
                 clearTokenStats();
             }
        } finally {
             hideLoading(); abortController = null;
        }
     }

    function renderChatHistory(historyArray) {
        chatHistory.innerHTML = '';
        if (Array.isArray(historyArray)) {
            historyArray.forEach(message => {
                appendMessage(message.role, message.content, false, true); // skipHistoryUpdate = true
            });
        }
        // Scroll after potentially adding many messages
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function appendMessage(role, content, isError = false, skipHistoryUpdate = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');

        if (isError) { messageDiv.classList.add('error-message'); messageDiv.innerHTML = `<strong>Error</strong> ${content}`; }
        else if (role === 'user') { messageDiv.classList.add('user-message'); messageDiv.textContent = content; }
        else if (role === 'assistant') { messageDiv.classList.add('assistant-message'); try { messageDiv.innerHTML = marked.parse(content || ""); } catch (e) { messageDiv.textContent = content; } }
        else { messageDiv.classList.add('system-message'); messageDiv.textContent = content; }

        chatHistory.appendChild(messageDiv);

        if (!skipHistoryUpdate) {
            chatHistory.scrollTop = chatHistory.scrollHeight; // Scroll only when adding single new messages
        }

        // Add to state if not skipping and not an error
        if (!skipHistoryUpdate && !isError) {
            if (Array.isArray(currentConversationHistory)) {
                currentConversationHistory.push({ role: role, content: content });
            } else {
                 console.error("Error: Cannot push message, currentConversationHistory is invalid.");
            }
        }
    }

    function updateTokenStats(usageData) {
        if (usageData && typeof usageData === 'object') {
            const promptTokens = usageData.prompt_tokens ?? 'N/A';
            const completionTokens = usageData.completion_tokens ?? 'N/A';
            const totalTokens = usageData.total_tokens ?? 'N/A';
            let durationSec = 'N/A';
            const totalDurationNs = usageData.total_duration;
            if (typeof totalDurationNs === 'number' && totalDurationNs > 0) {
                 durationSec = (totalDurationNs / 1_000_000_000).toFixed(2);
            }
            tokenStatsDisplay.textContent = `Prompt: ${promptTokens} | Comp: ${completionTokens} | Total: ${totalTokens} | Time: ${durationSec}s`;
        } else if (usageData === null) {
            tokenStatsDisplay.textContent = 'Usage stats not available';
        } else {
             clearTokenStats();
        }
    }

    function clearTokenStats() {
        tokenStatsDisplay.textContent = '';
    }

    function showLoading() {
        loadingIndicator.classList.remove('hidden');
        chatInput.disabled = true;
        sendButton.disabled = true;
    }

    function hideLoading() {
         loadingIndicator.classList.add('hidden');
         if (currentCandidateId) {
             chatInput.disabled = false;
             sendButton.disabled = false;
             chatInput.focus();
         } else {
             chatInput.disabled = true;
             sendButton.disabled = true;
         }
     }
});