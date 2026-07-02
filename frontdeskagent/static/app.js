const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatLog = document.getElementById("chatLog");

function addBubble(text, role) {
  if (!chatLog) return;
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
}

if (chatForm) {
  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;
    addBubble(message, "user");
    chatInput.value = "";
    addBubble("Thinking...", "agent");
    const pending = chatLog.lastElementChild;
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });
      const data = await response.json();
      pending.textContent = data.reply || data.error || "No reply returned.";
      if (data.model_error) {
        pending.textContent += `\n\nModel fallback: ${data.model_error}`;
      }
    } catch (error) {
      pending.textContent = `Request failed: ${error}`;
    }
  });
}
