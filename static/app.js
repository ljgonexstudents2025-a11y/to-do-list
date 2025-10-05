const list = document.getElementById("list");
const input = document.getElementById("newText");
const addBtn = document.getElementById("addBtn");

// Helper to call the API with JSON
async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok && res.status !== 204) {
    let msg = `HTTP ${res.status}`;
    try { const data = await res.json(); if (data.error) msg = data.error; } catch {}
    alert(msg);
    throw new Error(msg);
  }
  return res.status === 204 ? null : res.json();
}

// Load and render tasks
async function load() {
  const items = await api("/api/todos");
  render(items);
}

function render(items) {
  list.innerHTML = "";
  items.forEach((t) => {
    const li = document.createElement("li");
    if (t.done) li.classList.add("done");

    // checkbox
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = t.done;
    cb.onchange = async () => {
      await api(`/api/todos/${t.id}`, {
        method: "PATCH",
        body: JSON.stringify({ done: cb.checked }),
      });
      load();
    };

    // editable text
    const span = document.createElement("span");
    span.textContent = t.text;
    span.contentEditable = true;
    span.onblur = async () => {
      const newText = span.textContent.trim();
      if (newText && newText !== t.text) {
        await api(`/api/todos/${t.id}`, {
          method: "PATCH",
          body: JSON.stringify({ text: newText }),
        });
        load();
      }
    };

    // delete button
    const del = document.createElement("button");
    del.textContent = "Delete";
    del.onclick = async () => {
      await api(`/api/todos/${t.id}`, { method: "DELETE" });
      load();
    };

    li.append(cb, span, del);
    list.append(li);
  });
}

// Add new task
addBtn.onclick = async () => {
  const text = input.value.trim();
  if (!text) return;
  await api("/api/todos", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  input.value = "";
  load();
};

load();
