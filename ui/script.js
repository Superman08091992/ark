document.getElementById("chat-form").addEventListener("submit", async function (e) {
  e.preventDefault();
  const prompt = document.getElementById("prompt").value;
  const responseBox = document.getElementById("response");
  responseBox.textContent = "Thinking...";
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
    const data = await res.json();
    responseBox.textContent = data.reply || "[No reply]";
  } catch (err) {
    responseBox.textContent = "Error: " + err.message;
  }
});
