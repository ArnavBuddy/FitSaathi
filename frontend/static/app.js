(function () {
  console.log("FitSaathi: Initializing...");

  let userId = localStorage.getItem("fitSaathi_userId");
  if (!userId) {
    userId = "user_" + Math.random().toString(36).substr(2, 9);
    localStorage.setItem("fitSaathi_userId", userId);
  }

  const API_BASE = "/api";
  let currentScanResult = null;
  let sessionId = Math.random().toString(36).substr(2, 9);

  document.addEventListener("DOMContentLoaded", () => {
    console.log("FitSaathi: DOM Loaded");

    // UI Elements
    const elements = {
      uploadZone: document.getElementById("uploadZone"),
      fileInput: document.getElementById("fileInput"),
      scanBtn: document.getElementById("scanBtn"),
      loadingSpinner: document.getElementById("loadingSpinner"),
      recommendationsGrid: document.getElementById("recommendationsGrid"),
      filterBar: document.getElementById("filterBar"),
      findFitsBtn: document.getElementById("findFitsBtn"),
      chatPanel: document.getElementById("chatPanel"),
      chatTrigger: document.getElementById("chatTrigger"),
      chatMessages: document.getElementById("chatMessages"),
      chatInput: document.getElementById("chatInput"),
      sendChatBtn: document.getElementById("sendChatBtn"),
      closeChat: document.getElementById("closeChat"),
      genderFilter: document.getElementById("genderFilter"),
      budgetFilter: document.getElementById("budgetFilter"),
      budgetValue: document.getElementById("budgetValue"),
      occasionFilter: document.getElementById("occasionFilter"),
    };

    // Basic check for essential elements
    for (const [key, el] of Object.entries(elements)) {
      if (!el) {
        console.warn(`FitSaathi: Element #${key} not found in DOM.`);
      }
    }

    // Check if we are a demo user and show filter bar automatically
    if (elements.filterBar && userId && userId.startsWith("demo_user")) {
      console.log("FitSaathi: Demo user detected, showing filter bar");
      elements.filterBar.classList.add("active");

      // Auto-load recommendations for demo users
      setTimeout(() => {
        if (elements.findFitsBtn) {
          elements.findFitsBtn.click();
        }
      }, 500);
    }

    // Upload Logic
    if (elements.uploadZone && elements.fileInput) {
      elements.uploadZone.addEventListener("click", () =>
        elements.fileInput.click(),
      );
      elements.fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (e) => {
            elements.uploadZone.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; border-radius: 8px;">`;
          };
          reader.readAsDataURL(file);
        }
      });
    }

    if (elements.scanBtn) {
      elements.scanBtn.addEventListener("click", async () => {
        const file = elements.fileInput.files[0];
        if (!file) return alert("Please upload a photo first");

        const formData = new FormData();
        formData.append("file", file);
        formData.append("user_id", userId);

        elements.scanBtn.disabled = true;
        if (elements.loadingSpinner)
          elements.loadingSpinner.style.display = "block";

        try {
          const response = await fetch(`${API_BASE}/scan`, {
            method: "POST",
            body: formData,
          });
          const result = await response.json();

          if (result.error) {
            alert(result.message);
          } else {
            currentScanResult = result;
            if (elements.filterBar) elements.filterBar.classList.add("active");
            displayScanResult(result);
            loadRecommendations();
          }
        } catch (err) {
          console.error("FitSaathi Scan Error:", err);
          alert(
            "Failed to analyze scan. Please check your internet connection.",
          );
        } finally {
          elements.scanBtn.disabled = false;
          if (elements.loadingSpinner)
            elements.loadingSpinner.style.display = "none";
        }
      });
    }

    function displayScanResult(result) {
      if (!elements.uploadZone) return;
      const existing = document.getElementById("scan-summary");
      if (existing) existing.remove();

      const summary = document.createElement("div");
      summary.id = "scan-summary";
      summary.innerHTML = `
                <div style="margin-top: 20px; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 12px;">
                    <h3 style="color: var(--gold)">Analysis Complete</h3>
                    <p>Body Type: <strong>${(result.body_type || "unknown").toUpperCase()}</strong> | Confidence: ${((result.confidence_score || 0) * 100).toFixed(0)}%</p>
                    <p style="font-size: 14px; opacity: 0.8">${result.analysis_notes || ""}</p>
                </div>
            `;
      elements.uploadZone.parentNode.appendChild(summary);
    }

    // Recommendations
    async function loadRecommendations() {
      console.log("FitSaathi: Find My Fits clicked!");
      if (!elements.recommendationsGrid) {
        console.error("FitSaathi: recommendationsGrid not found");
        return;
      }

      const gender = elements.genderFilter
        ? elements.genderFilter.value
        : "unisex";
      const budget = elements.budgetFilter ? elements.budgetFilter.value : 5000;
      const occasion = elements.occasionFilter
        ? elements.occasionFilter.value
        : "";

      // Show loading state
      elements.recommendationsGrid.innerHTML =
        '<p style="text-align: center; padding: 40px;">Loading recommendations...</p>';

      try {
        console.log("FitSaathi: Fetching from API...");
        const filters = {
          gender: gender,
          budget_max: parseInt(budget),
        };

        if (occasion) {
          filters.style_tags = [occasion];
        }

        const response = await fetch(`${API_BASE}/recommend`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId,
            scan_result: currentScanResult,
            filters: filters,
          }),
        });

        console.log("FitSaathi: API Response Status:", response.status);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const items = await response.json();
        console.log("FitSaathi: Items received:", items);
        displayRecommendations(items);
      } catch (err) {
        console.error("FitSaathi Recommendations Error:", err);
        elements.recommendationsGrid.innerHTML = `<p style="text-align: center; padding: 40px; color: #E8705A;">Error loading recommendations: ${err.message}</p>`;
      }
    }

    if (elements.findFitsBtn) {
      console.log("FitSaathi: Binding findFitsBtn listener");
      elements.findFitsBtn.addEventListener("click", (e) => {
        console.log("FitSaathi: Button was clicked!");
        loadRecommendations();
      });
    }

    function displayRecommendations(items) {
      if (!elements.recommendationsGrid) return;
      elements.recommendationsGrid.innerHTML = "";
      if (!Array.isArray(items)) return;

      items.forEach((item, index) => {
        const card = document.createElement("div");
        card.className = "card";
        card.style.animationDelay = `${index * 0.1}s`;
        card.innerHTML = `
                    <img src="${item.image_url}" alt="${item.name}" onerror="this.src='https://via.placeholder.com/400x500?text=No+Image'">
                    <div class="card-content">
                        <div class="card-brand">${item.brand}</div>
                        <h4 class="card-title">${item.name}</h4>
                        <div class="price">₹${item.price_inr} <span class="size-badge">Your Size: ${item.size_recommendation}</span></div>
                        <div class="fit-score-bar">
                            <div class="fit-score-fill" style="width: ${item.fit_score}%"></div>
                        </div>
                        <p class="why-fits">${item.why_it_fits}</p>
                        <div class="card-actions">
                            <button class="btn btn-small like-btn" data-id="${item.item_id}">♡</button>
                            <button class="btn btn-small dislike-btn" data-id="${item.item_id}">✕</button>
                            <button class="btn btn-small" style="flex: 1">Try It</button>
                        </div>
                    </div>
                `;
        elements.recommendationsGrid.appendChild(card);
      });

      // Add feedback listeners
      elements.recommendationsGrid
        .querySelectorAll(".like-btn")
        .forEach((btn) => {
          btn.addEventListener("click", () =>
            handleFeedback(btn.dataset.id, "like"),
          );
        });
      elements.recommendationsGrid
        .querySelectorAll(".dislike-btn")
        .forEach((btn) => {
          btn.addEventListener("click", () =>
            handleFeedback(btn.dataset.id, "dislike"),
          );
        });
    }

    async function handleFeedback(itemId, action) {
      try {
        await fetch(`${API_BASE}/feedback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, item_id: itemId, action }),
        });
      } catch (err) {
        console.error("Feedback error:", err);
      }
    }

    // Chat Logic
    if (elements.chatTrigger && elements.chatPanel) {
      elements.chatTrigger.addEventListener("click", () =>
        elements.chatPanel.classList.toggle("active"),
      );
    }
    if (elements.closeChat) {
      elements.closeChat.addEventListener("click", () =>
        elements.chatPanel.classList.remove("active"),
      );
    }

    async function sendChatMessage() {
      if (!elements.chatInput) return;
      const message = elements.chatInput.value.trim();
      if (!message) return;

      addMessage(message, "user");
      elements.chatInput.value = "";

      try {
        const response = await fetch(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId,
            message,
            session_id: sessionId,
          }),
        });
        const result = await response.json();
        addMessage(result.response, "agent");
      } catch (err) {
        addMessage("Sorry, something went wrong with the chat.", "agent");
      }
    }

    function addMessage(text, sender) {
      if (!elements.chatMessages) return;
      const div = document.createElement("div");
      div.className = `message ${sender}`;
      div.textContent = text;
      elements.chatMessages.appendChild(div);
      elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    if (elements.sendChatBtn) {
      elements.sendChatBtn.addEventListener("click", sendChatMessage);
    }
    if (elements.chatInput) {
      elements.chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendChatMessage();
      });
    }

    // Update budget display
    if (elements.budgetFilter && elements.budgetValue) {
      elements.budgetFilter.addEventListener("input", (e) => {
        elements.budgetValue.textContent = `₹${e.target.value}`;
      });
    }
  });
})();
