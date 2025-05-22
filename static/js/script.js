document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = '/api'; // Updated to use relative path

    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    const emailsDataEl = document.getElementById('emails-data');
    const chatsDataEl = document.getElementById('chats-data');
    const actionsListEl = document.getElementById('actions-list');

    const actionDetailsPanel = document.getElementById('action-details-panel');
    const actionDetailsContentEl = document.getElementById('action-details-content');
    const closePanelButton = document.getElementById('close-panel-button');

    let allActionsData = []; // To store fetched actions with full details

    // Tab switching logic
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const targetTabContent = document.getElementById(`${tab.dataset.tab}-content`);
            tabContents.forEach(tc => tc.classList.remove('active'));
            targetTabContent.classList.add('active');

            if (tab.dataset.tab === 'data' && emailsDataEl.textContent === 'Loading emails...') {
                fetchRawData();
            } else if (tab.dataset.tab === 'actions' && actionsListEl.innerHTML === '') {
                fetchActions();
            }
        });
    });

    // Function to fetch raw data
    async function fetchRawData() {
        try {
            const response = await fetch(`${API_BASE_URL}/raw-data`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            emailsDataEl.textContent = JSON.stringify(data.emails, null, 2);
            chatsDataEl.textContent = JSON.stringify(data.chats, null, 2);
        } catch (error) {
            console.error("Error fetching raw data:", error);
            emailsDataEl.textContent = "Failed to load email data.";
            chatsDataEl.textContent = "Failed to load chat data.";
        }
    }

    // Function to fetch actions
    async function fetchActions() {
        try {
            const response = await fetch(`${API_BASE_URL}/dia/context-actions`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            allActionsData = await response.json(); // Store full data

            renderActions(allActionsData);
        } catch (error) {
            console.error("Error fetching actions:", error);
            actionsListEl.innerHTML = "<p>Failed to load actions.</p>";
        }
    }

    // Function to fetch action details
    async function fetchActionDetails(actionId, actionData) {
        try {
            const response = await fetch(`${API_BASE_URL}/dia/execute-action/${actionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(actionData)
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Error fetching action details:", error);
            throw error;
        }
    }

    // Function to render actions in the list
    function renderActions(actions) {
        actionsListEl.innerHTML = ''; // Clear previous actions
        if (actions.length === 0) {
            actionsListEl.innerHTML = `
                <div class="empty-state">
                    <span class="material-icons empty-icon">search_off</span>
                    <p>No actions suggested at the moment.</p>
                </div>
            `;
            return;
        }

        actions.forEach(action => {
            const actionItem = document.createElement('div');
            actionItem.classList.add('action-item');
            actionItem.setAttribute('data-action-id', action.id);
            
            // Determine icon based on source type
            let typeIcon = action.source_type === 'Email' ? 'email' : 'chat';
            
            actionItem.innerHTML = `
                <h4>
                    <span class="material-icons action-icon">${typeIcon}</span>
                    ${action.action_title}
                </h4>
                <p><span class="source-label">Source Type:</span> ${action.source_type}</p>
                <p><span class="source-label">Source:</span> ${action.source_summary}</p>
                <div class="action-button">
                    <span class="material-icons">arrow_forward</span>
                </div>
            `;
            actionItem.addEventListener('click', () => openActionDetails(action));
            actionsListEl.appendChild(actionItem);
        });
    }

    // Function to open action details panel
    async function openActionDetails(action) {
        // Show loading state
        actionDetailsContentEl.innerHTML = `
            <h3>${action.action_title}</h3>
            <div class="detail-section">
                <strong>Source Type:</strong> ${action.source_type}
            </div>
            <div class="detail-section">
                <strong>Full Source Data:</strong>
                <pre>${JSON.stringify(action.source_full, null, 2)}</pre>
            </div>
            <div class="detail-section">
                <strong>Input for LLM2 (Action Details):</strong>
                <pre>${action.details_for_llm2}</pre>
            </div>
            <div class="detail-section" id="dia-execution-output">
                <strong>Dia's Execution Plan & Analysis:</strong>
                <div class="loading">Loading Dia's analysis...</div>
            </div>
        `;
        actionDetailsPanel.classList.add('open');

        try {
            // Fetch the action details
            const result = await fetchActionDetails(action.id, action);
            const outputContainer = actionDetailsContentEl.querySelector('#dia-execution-output');

            if (result.error) {
                outputContainer.innerHTML = `
                    <strong>Dia's Execution Plan & Analysis:</strong>
                    <div class="error">Failed to process action: ${result.error}</div>
                    ${result.details ? `<pre>${JSON.stringify(result.details, null, 2)}</pre>` : '' }
                `;
                return;
            }

            // Extract the research_result object from the response
            const research = result.research_result;
            
            let outputHTML = `<strong>Dia's Execution Plan & Analysis:</strong>`;
            
            if (research.plan) {
                outputHTML += `
                    <h4>Execution Plan:</h4>
                    <pre class="plan-steps">${research.plan.replace(/\n/g, '<br>')}</pre>
                `;
            }

            if (research.found_data && Object.keys(research.found_data).length > 0) {
                outputHTML += `
                    <h4>Retrieved Personal Data:</h4>
                    <pre>${JSON.stringify(research.found_data, null, 2)}</pre>
                `;
            }

            if (research.missing_data_keys && research.missing_data_keys.length > 0) {
                outputHTML += `
                    <h4>Missing Personal Data:</h4>
                    <ul class="missing-keys-list">
                        ${research.missing_data_keys.map(key => `<li>${key}</li>`).join('')}
                    </ul>
                    <p><em>Dia will proceed with the available information, but you might need to provide the missing items.</em></p>
                `;
            }
            
            if (research.summary) {
                 outputHTML += `
                    <h4>Dia's Summary:</h4>
                    <pre class="summary-text">${research.summary.replace(/\n/g, '<br>')}</pre>
                `;
            }
            
            if (research.error_details && research.summary && research.summary.startsWith("Error:")) {
                 outputHTML += `
                    <h4>Error Details:</h4>
                    <pre>${JSON.stringify(research.error_details, null, 2)}</pre>
                `;
            }

            outputContainer.innerHTML = outputHTML;

        } catch (error) {
            const outputContainer = actionDetailsContentEl.querySelector('#dia-execution-output');
            outputContainer.innerHTML = `
                <strong>Dia's Execution Plan & Analysis:</strong>
                <div class="error">Failed to load Dia's analysis. Please try again.</div>
            `;
        }
    }

    // Close panel button
    closePanelButton.addEventListener('click', () => {
        actionDetailsPanel.classList.remove('open');
    });

    // Load data for the initially active tab
    const activeInitialTab = document.querySelector('.tab-button.active');
    if (activeInitialTab) {
        if (activeInitialTab.dataset.tab === 'data') {
            fetchRawData();
        } else if (activeInitialTab.dataset.tab === 'actions') {
            fetchActions();
        }
    } else { // Default to loading data tab if none explicitly active
        fetchRawData();
    }
});
