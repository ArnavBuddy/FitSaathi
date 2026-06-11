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
  let currentTryOnItem = null;
  let currentTryOnJobId = null;
  let isDragging = false;
  let isResizing = false;
  let startX = 0;
  let startY = 0;
  let currentX = 0;
  let currentY = 0;
  let currentScale = 1;
  let startScale = 1;
  let itemsData = [];
  let isUsingNewTryOn = false;

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
      tryOnModal: document.getElementById("tryOnModal"),
      closeTryOn: document.getElementById("closeTryOn"),
      tryOnItemName: document.getElementById("tryOnItemName"),
      tryOnPhotoInput: document.getElementById("tryOnPhotoInput"),
      tryOnUserPhoto: document.getElementById("tryOnUserPhoto"),
      tryOnProductPhoto: document.getElementById("tryOnProductPhoto"),
      tryOnProductWrapper: document.getElementById("tryOnProductWrapper"),
      resizeHandle: document.getElementById("resizeHandle"),
      tryOnPlaceholder: document.getElementById("tryOnPlaceholder"),
      tryOnSizeSlider: document.getElementById("tryOnSizeSlider"),
      tryOnContainer: document.getElementById("tryOnContainer"),
      tryOnResultPhoto: document.getElementById("tryOnResultPhoto"),
      tryOnLoading: document.getElementById("tryOnLoading"),
      tryOnGenerateBtn: document.getElementById("tryOnGenerateBtn"),
      tryOnDownloadBtn: document.getElementById("tryOnDownloadBtn"),
      tryOnManualControls: document.getElementById("tryOnManualControls"),
      tryOnControls: document.getElementById("tryOnControls"),
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
                    <h3 style="color: var(--gold);">Analysis Complete</h3>
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

        itemsData = await response.json();
        console.log("FitSaathi: Items received:", itemsData);
        displayRecommendations(itemsData);
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
                            <button class="btn btn-small try-it-btn" data-index="${index}" style="flex: 1;">Try It</button>
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
      // Add Try It listeners - using index instead of data-item
      elements.recommendationsGrid
        .querySelectorAll(".try-it-btn")
        .forEach((btn) => {
          btn.addEventListener("click", () => {
            const index = parseInt(btn.dataset.index);
            const item = itemsData[index];
            openTryOnModal(item);
          });
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

    // Virtual Try-On Functions
    function openTryOnModal(item) {
      currentTryOnItem = item;
      currentTryOnJobId = null;
      isUsingNewTryOn = false;
      
      elements.tryOnItemName.textContent = item.name;
      elements.tryOnProductPhoto.src = item.image_url;
      
      // Reset all displays
      elements.tryOnProductWrapper.style.display = "block";
      elements.tryOnUserPhoto.style.display = "none";
      elements.tryOnPlaceholder.style.display = "block";
      elements.tryOnResultPhoto.style.display = "none";
      elements.tryOnLoading.style.display = "none";
      elements.tryOnGenerateBtn.style.display = "none";
      elements.tryOnDownloadBtn.style.display = "none";
      elements.tryOnManualControls.style.display = "flex";
      
      elements.tryOnPhotoInput.value = "";
      elements.tryOnSizeSlider.value = 1;
      currentScale = 1;
      resetProductPosition();
      elements.tryOnModal.style.display = "flex";
    }

    function resetProductPosition() {
      currentX = 0;
      currentY = 0;
      currentScale = 1;
      elements.tryOnProductWrapper.style.transform =
        "translate(-50%, 0) scale(1)";
      elements.tryOnProductWrapper.style.top = "15%";
      elements.tryOnProductWrapper.style.left = "50%";
      elements.tryOnProductWrapper.style.width = "60%";
    }

    function closeTryOnModal() {
      elements.tryOnModal.style.display = "none";
      currentTryOnItem = null;
      currentTryOnJobId = null;
    }

    async function handleTryOnPhotoUpload(e) {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = async (e) => {
        elements.tryOnUserPhoto.src = e.target.result;
        elements.tryOnUserPhoto.style.display = "block";
        elements.tryOnPlaceholder.style.display = "none";
        elements.tryOnGenerateBtn.style.display = "block";
        elements.tryOnGenerateBtn.disabled = false;
      };
      reader.readAsDataURL(file);
    }
    
    async function handleGenerateTryOn() {
      if (!currentTryOnItem || !elements.tryOnPhotoInput.files[0]) {
        alert("Please select an item and upload your photo!");
        return;
      }
      
      isUsingNewTryOn = true;
      elements.tryOnLoading.style.display = "flex";
      elements.tryOnGenerateBtn.disabled = true;
      elements.tryOnProductWrapper.style.display = "none";
      elements.tryOnManualControls.style.display = "none";
      
      try {
        const formData = new FormData();
        formData.append("user_id", userId);
        formData.append("item_id", currentTryOnItem.item_id);
        formData.append("file", elements.tryOnPhotoInput.files[0]);
        
        console.log("Sending request to /api/v1/tryon/generate...");
        
        const response = await fetch("/api/v1/tryon/generate", {
          method: "POST",
          body: formData,
        });
        
        if (!response.ok) {
          throw new Error("Failed to start try-on generation");
        }
        
        const result = await response.json();
        currentTryOnJobId = result.job_id;
        
        console.log("Job started, polling for result:", currentTryOnJobId);
        
        // Poll for results
        pollTryOnResult(currentTryOnJobId);
        
      } catch (err) {
        console.error("Error generating try-on:", err);
        alert("Error generating try-on, falling back to manual mode!");
        elements.tryOnLoading.style.display = "none";
        elements.tryOnGenerateBtn.style.display = "block";
        elements.tryOnGenerateBtn.disabled = false;
        elements.tryOnProductWrapper.style.display = "block";
        elements.tryOnManualControls.style.display = "flex";
        
        // Fall back to original analyze and place
        await analyzeAndPlaceClothing(elements.tryOnPhotoInput.files[0]);
      }
    }
    
    async function pollTryOnResult(jobId) {
      const maxAttempts = 60;
      let attempts = 0;
      
      const poll = async () => {
        try {
          const response = await fetch(`/api/v1/tryon/result/${jobId}`);
          
          if (!response.ok) {
            throw new Error("Failed to check job status");
          }
          
          const job = await response.json();
          
          console.log("Job status:", job);
          
          if (job.status === "completed" && job.generated_image) {
            // Success! Display result
            elements.tryOnLoading.style.display = "none";
            elements.tryOnResultPhoto.src = job.generated_image;
            elements.tryOnResultPhoto.style.display = "block";
            elements.tryOnDownloadBtn.style.display = "block";
            console.log("Try-on completed successfully!");
            
          } else if (job.status === "failed") {
            throw new Error(job.error_message || "Try-on failed");
            
          } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 2000);
            
          } else {
            throw new Error("Try-on timed out");
          }
        } catch (err) {
          console.error("Polling error:", err);
          alert("Error with try-on, falling back to manual mode!");
          elements.tryOnLoading.style.display = "none";
          elements.tryOnGenerateBtn.style.display = "block";
          elements.tryOnGenerateBtn.disabled = false;
          elements.tryOnProductWrapper.style.display = "block";
          elements.tryOnManualControls.style.display = "flex";
          
          await analyzeAndPlaceClothing(elements.tryOnPhotoInput.files[0]);
        }
      };
      
      poll();
    }
    
    async function analyzeAndPlaceClothing(file) {
      try {
        console.log("Analyzing photo for clothing placement...");
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_BASE}/analyze-placement`, {
          method: "POST",
          body: formData,
        });

        const analysis = await response.json();
        console.log("Placement analysis:", analysis);

        // Apply the placement
        if (analysis.placement) {
          const p = analysis.placement;
          elements.tryOnProductWrapper.style.top = `${p.top_percent}%`;
          elements.tryOnProductWrapper.style.left = `${p.left_percent}%`;
          elements.tryOnProductWrapper.style.width = `${p.width_percent}%`;
          elements.tryOnProductWrapper.style.transform = `translate(-50%, 0) rotate(${p.rotation_degrees}deg) scale(1)`;
          elements.tryOnSizeSlider.value = p.width_percent / 60; // Normalize to 0.5-1.5 range
          currentScale = p.width_percent / 60;
          currentX = 0;
          currentY = 0;
        }

        alert(
          "Clothing placed automatically! You can drag or resize to adjust.",
        );
      } catch (err) {
        console.error("Error analyzing placement:", err);
        alert(
          "Could not automatically place clothing. You can adjust manually.",
        );
      }
    }

    function handleTryOnSizeChange(e) {
      currentScale = parseFloat(e.target.value);
      updateProductTransform();
    }

    function updateProductTransform() {
      elements.tryOnProductWrapper.style.transform = `translate(calc(-50% + ${currentX}px), ${currentY}px) scale(${currentScale})`;
    }

    // Drag functionality - now uses the wrapper
    function startDrag(e) {
      if (e.target === elements.resizeHandle) return;
      isDragging = true;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);

      startX = clientX - currentX;
      startY = clientY - currentY;
    }

    function doDrag(e) {
      if (!isDragging) return;
      e.preventDefault();

      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);

      currentX = clientX - startX;
      currentY = clientY - startY;

      updateProductTransform();
    }

    function endDrag() {
      isDragging = false;
    }

    // Resize functionality
    function startResize(e) {
      e.stopPropagation();
      isResizing = true;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);

      startX = clientX;
      startY = clientY;
      startScale = currentScale;
    }

    function doResize(e) {
      if (!isResizing) return;
      e.preventDefault();

      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);

      const deltaX = clientX - startX;
      const deltaY = clientY - startY;
      const delta = Math.max(deltaX, deltaY);

      // Calculate scale change
      const scaleChange = delta / 100; // Adjust sensitivity
      currentScale = Math.max(0.3, Math.min(2.5, startScale + scaleChange));

      elements.tryOnSizeSlider.value = currentScale;
      updateProductTransform();
    }

    function endResize() {
      isResizing = false;
    }
    
    function handleDownloadResult() {
      if (elements.tryOnResultPhoto.src) {
        const link = document.createElement("a");
        link.href = elements.tryOnResultPhoto.src;
        link.download = `fitsaathi-tryon-${currentTryOnItem.item_id}.jpg`;
        link.click();
      }
    }

    // Bind Try-On Events
    if (elements.closeTryOn) {
      elements.closeTryOn.addEventListener("click", closeTryOnModal);
    }
    if (elements.tryOnModal) {
      elements.tryOnModal.addEventListener("click", (e) => {
        if (e.target === elements.tryOnModal) {
          closeTryOnModal();
        }
      });
    }
    if (elements.tryOnPhotoInput) {
      elements.tryOnPhotoInput.addEventListener(
        "change",
        handleTryOnPhotoUpload,
      );
    }
    if (elements.tryOnSizeSlider) {
      elements.tryOnSizeSlider.addEventListener("input", handleTryOnSizeChange);
    }
    if (elements.tryOnGenerateBtn) {
      elements.tryOnGenerateBtn.addEventListener("click", handleGenerateTryOn);
    }
    if (elements.tryOnDownloadBtn) {
      elements.tryOnDownloadBtn.addEventListener("click", handleDownloadResult);
    }

    // Bind drag events to wrapper
    if (elements.tryOnProductWrapper) {
      elements.tryOnProductWrapper.addEventListener("mousedown", startDrag);
      document.addEventListener("mousemove", function (e) {
        doDrag(e);
        doResize(e);
      });
      document.addEventListener("mouseup", function () {
        endDrag();
        endResize();
      });

      // Touch events for mobile
      elements.tryOnProductWrapper.addEventListener("touchstart", startDrag, {
        passive: false,
      });
      document.addEventListener(
        "touchmove",
        function (e) {
          doDrag(e);
          doResize(e);
        },
        { passive: false },
      );
      document.addEventListener("touchend", function () {
        endDrag();
        endResize();
      });
    }

    // Bind resize events
    if (elements.resizeHandle) {
      elements.resizeHandle.addEventListener("mousedown", startResize);
      elements.resizeHandle.addEventListener("touchstart", startResize, {
        passive: false,
      });
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
