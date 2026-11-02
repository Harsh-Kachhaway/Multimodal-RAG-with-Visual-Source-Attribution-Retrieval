const questionInputField = document.getElementById("userQuestionInput");
const triggerSearchButton = document.getElementById("searchButton");
const answerDisplayElement = document.getElementById("answerContent");
const sourcesContainerElement = document.getElementById("sourcesContainer");
const diagramDisplayArea = document.getElementById("diagramDisplayArea");
const diagramCountBadge = document.getElementById("diagramCountBadge");
const relevanceBadge = document.getElementById("relevanceBadge");
const statusDot = document.getElementById("systemStatusDot");
const statusLabel = document.getElementById("systemStatusLabel");
const lightboxModal = document.getElementById("imageLightboxModal");
const modalFullImage = document.getElementById("modalFullImage");
const modalCaption = document.getElementById("modalCaption");
const closeModalButton = document.getElementById("closeModalButton");
const presetTopicChips = document.querySelectorAll(".topic-chip");

async function checkServerHealth() {
    try {
        const response = await fetch("/health");
        if (response.ok) {
            const healthData = await response.json();
            statusDot.className = "status-dot healthy";
            statusLabel.textContent = healthData.database_connected ? "Vector DB Connected" : "DB Degraded";
        } else {
            statusDot.className = "status-dot error";
            statusLabel.textContent = "API Error";
        }
    } catch (networkError) {
        statusDot.className = "status-dot error";
        statusLabel.textContent = "Offline";
    }
}

function openDiagramModal(imageUrl, captionText) {
    modalFullImage.src = imageUrl;
    modalCaption.textContent = captionText;
    lightboxModal.classList.remove("hidden");
}

function closeDiagramModal() {
    lightboxModal.classList.add("hidden");
    modalFullImage.src = "";
}

closeModalButton.addEventListener("click", closeDiagramModal);
lightboxModal.addEventListener("click", (event) => {
    if (event.target === lightboxModal) {
        closeDiagramModal();
    }
});

presetTopicChips.forEach((chip) => {
    chip.addEventListener("click", () => {
        const selectedQuestion = chip.getAttribute("data-question");
        questionInputField.value = selectedQuestion;
        performKnowledgeQuery(selectedQuestion);
    });
});

triggerSearchButton.addEventListener("click", () => {
    const userEnteredQuery = questionInputField.value.trim();
    if (userEnteredQuery) {
        performKnowledgeQuery(userEnteredQuery);
    }
});

questionInputField.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        const userEnteredQuery = questionInputField.value.trim();
        if (userEnteredQuery) {
            performKnowledgeQuery(userEnteredQuery);
        }
    }
});

async function performKnowledgeQuery(questionText) {
    answerDisplayElement.innerHTML = "<div style='color: #94a3b8;'>Synthesizing concepts from textbook vectors and compiling visual evidence...</div>";
    sourcesContainerElement.innerHTML = "";
    diagramDisplayArea.innerHTML = "";
    relevanceBadge.textContent = "Synthesizing...";
    triggerSearchButton.disabled = true;

    try {
        const response = await fetch("/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question: questionText })
        });

        if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        
        answerDisplayElement.innerHTML = data.answer.replace(/\n\n/g, "<br><br>").replace(/\n/g, "<br>");
        relevanceBadge.textContent = "Synthesis Ready";

        renderTextbookSources(data.sources || []);
        renderTextbookDiagrams(data.sources || [], data.images || []);

    } catch (error) {
        answerDisplayElement.innerHTML = `<div style="color: #ef4444;">Failed to retrieve textbook content: ${error.message}</div>`;
        relevanceBadge.textContent = "Query Failed";
    } finally {
        triggerSearchButton.disabled = false;
    }
}

function renderTextbookSources(sourcesList) {
    sourcesContainerElement.innerHTML = "";
    
    if (sourcesList.length === 0) {
        sourcesContainerElement.innerHTML = "<div style='color: #64748b;'>No matching textbook sections found.</div>";
        return;
    }

    sourcesList.forEach((source, index) => {
        const metadata = source.metadata || {};
        const topic = metadata.topic || "Civic Concept";
        const subtopic = metadata.subtopic || "Principles";
        const score = source.score ? `${(source.score * 100).toFixed(1)}% Match` : "Retrieved";

        const card = document.createElement("div");
        card.className = "source-card";
        card.innerHTML = `
            <div class="source-header">
                <span class="source-meta-tag">Excerpt ${index + 1}: ${topic} · ${subtopic}</span>
                <span class="source-relevance">${score}</span>
            </div>
            <div class="source-text">${cleanSnippetText(source.text)}</div>
        `;
        sourcesContainerElement.appendChild(card);
    });
}

function cleanSnippetText(rawText) {
    return rawText
        .replace(/!\[(.*?)\]\((.+?\.(?:png|jpg|jpeg|webp|svg|gif|bmp)|[^\s\)]+)\)/g, "<em>[Visual Reference: $1]</em>")
        .replace(/\n\n/g, "<br><br>")
        .replace(/\n/g, "<br>");
}

function renderTextbookDiagrams(sourcesList, directImagesList) {
    diagramDisplayArea.innerHTML = "";
    const collectedDiagrams = [];

    sourcesList.forEach((source) => {
        const metadata = source.metadata || {};
        let imageUrl = source.image_url || metadata.image_url;
        let caption = source.image_caption || metadata.image_caption || "Textbook Figure";
        let topic = metadata.topic || "Visual Evidence";

        if (imageUrl) {
            if (!imageUrl.startsWith("http") && !imageUrl.startsWith("/images")) {
                const filename = imageUrl.split("/").pop();
                imageUrl = `/images/${filename}`;
            }
            if (!collectedDiagrams.some(item => item.url === imageUrl)) {
                collectedDiagrams.push({ url: imageUrl, caption: caption, topic: topic });
            }
        }
    });

    directImagesList.forEach((directUrl) => {
        if (!collectedDiagrams.some(item => item.url === directUrl)) {
            collectedDiagrams.push({
                url: directUrl,
                caption: "Referenced Figure",
                topic: "Diagram Document"
            });
        }
    });

    diagramCountBadge.textContent = `${collectedDiagrams.length} Visual${collectedDiagrams.length === 1 ? "" : "s"}`;

    if (collectedDiagrams.length === 0) {
        diagramDisplayArea.innerHTML = `
            <div class="empty-diagram-state">
                <div class="empty-icon">📖</div>
                <p>No diagrams are linked directly to this specific concept. Try asking about Belgian communities or Sri Lankan ethnic groups.</p>
            </div>
        `;
        return;
    }

    collectedDiagrams.forEach((diagram) => {
        const card = document.createElement("div");
        card.className = "diagram-card";
        card.innerHTML = `
            <img class="diagram-image" src="${diagram.url}" alt="${diagram.caption}" loading="lazy">
            <div class="diagram-info">
                <div class="diagram-topic">${diagram.topic}</div>
                <div class="diagram-label">${diagram.caption}</div>
            </div>
        `;
        card.addEventListener("click", () => {
            openDiagramModal(diagram.url, `${diagram.topic}: ${diagram.caption}`);
        });
        diagramDisplayArea.appendChild(card);
    });
}

checkServerHealth();
const initialQuery = questionInputField.value.trim();
if (initialQuery) {
    performKnowledgeQuery(initialQuery);
}

