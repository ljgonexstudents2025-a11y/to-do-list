// Grab DOM elements
const textInput = document.getElementById("newText");
const dueDateInput = document.getElementById("dueDate");
const categorySelect = document.getElementById("category");
const addBtn = document.getElementById("addBtn");
const listEl = document.getElementById("list");
const counterEl = document.getElementById("counter");
const clearCompletedBtn = document.getElementById("clearCompleted");
const filtersContainer = document.querySelector(".filters");
const todayEl = document.getElementById("today");

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("hamburger");
  const menu = document.getElementById("hamburger-menu");

  if (!btn || !menu) return;

  // toggle on button click
  btn.addEventListener("click", (event) => {
    event.stopPropagation(); // don't trigger document click
    menu.classList.toggle("is-open");
  });

  // close when clicking anywhere else
  document.addEventListener("click", (event) => {
    if (!menu.classList.contains("is-open")) return;

    const clickInside =
      menu.contains(event.target) || btn.contains(event.target);

    if (!clickInside) {
      menu.classList.remove("is-open");
    }
  });
});


// In-memory list of todos (comes from the server)
let todos = [];
let currentFilter = "all";

// Show today's date and pre-fill date input
if (todayEl) {
  const today = new Date();
  todayEl.textContent = today.toLocaleDateString(undefined, {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

if (dueDateInput) {
  const todayStr = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  dueDateInput.value = todayStr;
}

// --- Event listeners ---

addBtn.addEventListener("click", handleAdd);

textInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    handleAdd();
  }
});

// Filter buttons (All / Active / Done)
if (filtersContainer) {
  filtersContainer.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-filter]");
    if (!btn) return;

    currentFilter = btn.dataset.filter;

    // Update active class
    document
      .querySelectorAll(".filters button")
      .forEach((b) => b.classList.toggle("active", b === btn));

    render();
  });
}

// Clear completed button
clearCompletedBtn.addEventListener("click", async () => {
  const doneTodos = todos.filter((t) => t.done);
  await Promise.all(
    doneTodos.map((todo) =>
      fetch(`/api/todos/${todo.id}`, { method: "DELETE" })
    )
  );
  await loadTodos();
});

// --- Core functions ---

// Load all todos from the API
async function loadTodos() {
  const res = await fetch("/api/todos");
  if (!res.ok) {
    console.error("Failed to load todos");
    return;
  }
  todos = await res.json();
  render();
}

// Add a new todo
async function handleAdd() {
  const text = textInput.value.trim();
  if (!text) return;

  const due_date = dueDateInput.value || null;
  const category = categorySelect.value || null;

  const res = await fetch("/api/todos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, due_date, category }),
  });

  if (!res.ok) {
    console.error("Failed to add todo");
    return;
  }

  textInput.value = "";
  // optionally keep the date & category as they are
  await loadTodos();
}

// Toggle done / not done
async function toggleDone(todo) {
  const res = await fetch(`/api/todos/${todo.id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ done: !todo.done }),
  });

  if (!res.ok) {
    console.error("Failed to toggle todo");
    return;
  }

  // Update local copy
  todo.done = !todo.done;
  render();
}

// Delete a todo
async function deleteTodo(todo) {
  const res = await fetch(`/api/todos/${todo.id}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    console.error("Failed to delete todo");
    return;
  }

  todos = todos.filter((t) => t.id !== todo.id);
  render();
}

// Edit text (click the text)
async function editTodoText(todo) {
  const newText = prompt("Edit task:", todo.text);
  if (!newText) return;
  const trimmed = newText.trim();
  if (!trimmed || trimmed === todo.text) return;

  const res = await fetch(`/api/todos/${todo.id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: trimmed }),
  });

  if (!res.ok) {
    console.error("Failed to update todo text");
    return;
  }

  todo.text = trimmed;
  render();
}

// Render list + counter
function render() {
  listEl.innerHTML = "";

  let visibleTodos = todos;
  if (currentFilter === "active") {
    visibleTodos = todos.filter((t) => !t.done);
  } else if (currentFilter === "done") {
    visibleTodos = todos.filter((t) => t.done);
  }

  visibleTodos.forEach((todo) => {
    const li = document.createElement("li");
    if (todo.done) {
      li.classList.add("done");
    }

    // Checkbox for done/undone
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.done;
    checkbox.addEventListener("change", () => toggleDone(todo));

    // Text + meta container
    const content = document.createElement("div");
    content.className = "todo-content";

    // Main text
    const textSpan = document.createElement("span");
    textSpan.textContent = todo.text;
    textSpan.addEventListener("click", () => editTodoText(todo));

    content.appendChild(textSpan);

    // Meta info: due date + category
    if (todo.due_date || todo.category) {
      const meta = document.createElement("div");
      meta.className = "todo-meta";

      if (todo.due_date) {
        const dd = document.createElement("span");
        dd.textContent = `Due: ${todo.due_date}`;
        meta.appendChild(dd);
      }

      if (todo.category) {
        const cat = document.createElement("span");
        cat.className = "badge";
        cat.textContent = todo.category;
        meta.appendChild(cat);
      }

      content.appendChild(meta);
    }

    // Delete button
    const delBtn = document.createElement("button");
    delBtn.textContent = "✕";
    delBtn.className = "delete-btn";
    delBtn.addEventListener("click", () => deleteTodo(todo));

    li.appendChild(checkbox);
    li.appendChild(content);
    li.appendChild(delBtn);
    listEl.appendChild(li);
  });

  // Counter: tasks left
  const activeCount = todos.filter((t) => !t.done).length;
  if (counterEl) {
    counterEl.textContent = `${activeCount} task${
      activeCount === 1 ? "" : "s"
    } left`;
  }
}

// Initial load
loadTodos();
