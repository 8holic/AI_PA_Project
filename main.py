import tkinter as tk
from tkinter import simpledialog, ttk, messagebox
import sqlite3
import os
import threading
import ollama

# -----------------------------
# MODEL & SYSTEM PROMPT
# -----------------------------
model = "dolphin-mixtral"

# Load system prompt from a text file
prompt_file = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
try:
    with open(prompt_file, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a helpful assistant. Answer politely and concisely."
print("Loaded system prompt:", SYSTEM_PROMPT)
# -----------------------------
# DATABASE SETUP (thread-safe)
# -----------------------------
if not os.path.exists("Conversation_History"):
    os.makedirs("Conversation_History")

db_path = "Conversation_History/conversations.db"

conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    role TEXT,
    content TEXT
)
""")
conn.commit()

# -----------------------------
# GLOBAL STATE
# -----------------------------
conversation_id = None
messages = []

# -----------------------------
# DATABASE HELPERS
# -----------------------------
def get_conversations():
    cursor.execute("SELECT name FROM conversations")
    rows = cursor.fetchall()
    return [r[0] for r in rows]

def load_conversation(name):
    global conversation_id, messages
    chat_box.delete("1.0", tk.END)

    cursor.execute("SELECT id FROM conversations WHERE name=?", (name,))
    row = cursor.fetchone()
    if not row:
        return
    conversation_id = row[0]

    cursor.execute(
        "SELECT role, content FROM messages WHERE conversation_id=?",
        (conversation_id,)
    )
    rows = cursor.fetchall()
    messages = []

    # add system prompt
    messages.append({"role": "system", "content": SYSTEM_PROMPT})

    for role, content in rows:
        messages.append({"role": role, "content": content})
        if role == "user":
            chat_box.insert(tk.END, "You: " + content + "\n")
        else:
            chat_box.insert(tk.END, "AI: " + content + "\n\n")

def save_message(role, text):
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, text)
    )
    conn.commit()

# -----------------------------
# NEW CONVERSATION
# -----------------------------
def new_conversation():
    name = simpledialog.askstring("New Conversation", "Conversation name:")
    if not name:
        return

    cursor.execute("INSERT OR IGNORE INTO conversations (name) VALUES (?)", (name,))
    conn.commit()
    refresh_dropdown()
    load_conversation(name)
    selected_conversation.set(name)

# -----------------------------
# DELETE CONVERSATION
# -----------------------------
def delete_conversation():
    global conversation_id, messages
    name = selected_conversation.get()
    if not name:
        return
    
    confirm = messagebox.askyesno("Delete Conversation", f"Are you sure you want to delete '{name}'?")
    if not confirm:
        return

    # delete messages
    cursor.execute(
        "DELETE FROM messages WHERE conversation_id = (SELECT id FROM conversations WHERE name=?)",
        (name,)
    )
    # delete conversation
    cursor.execute(
        "DELETE FROM conversations WHERE name=?",
        (name,)
    )
    conn.commit()

    # reset UI
    messages = []
    conversation_id = None
    chat_box.delete("1.0", tk.END)
    refresh_dropdown()

    # select first conversation if any remain
    conversations = get_conversations()
    if conversations:
        select_conversation(conversations[0])
    else:
        selected_conversation.set("")

# -----------------------------
# DROPDOWN HANDLING
# -----------------------------
def refresh_dropdown():
    menu = dropdown["menu"]
    menu.delete(0, "end")
    for conv in get_conversations():
        menu.add_command(
            label=conv,
            command=lambda value=conv: select_conversation(value)
        )

def select_conversation(name):
    selected_conversation.set(name)
    load_conversation(name)

# -----------------------------
# AI HANDLER WITH THREADING
# -----------------------------
def send_message():
    if conversation_id is None:
        return

    user_text = entry.get()
    entry.delete(0, tk.END)

    chat_box.insert(tk.END, "You: " + user_text + "\n")
    messages.append({"role": "user", "content": user_text})
    save_message("user", user_text)

    spinner.start()
    thread = threading.Thread(target=run_ai, args=(user_text,))
    thread.start()

def run_ai(user_text):
    response = ollama.chat(
        model=model,
        messages=messages
    )
    ai_text = response["message"]["content"]

    messages.append({"role": "assistant", "content": ai_text})
    save_message("assistant", ai_text)

    root.after(0, lambda: finish_ai(ai_text))

def finish_ai(ai_text):
    spinner.stop()
    chat_box.insert(tk.END, "AI: " + ai_text + "\n\n")

# -----------------------------
# GUI
# -----------------------------
root = tk.Tk()
root.title("Local Assistant")
root.geometry("800x600")
root.minsize(600, 400)

# --- Top bar
top_bar = tk.Frame(root)
top_bar.pack(fill=tk.X, pady=5, padx=5)

selected_conversation = tk.StringVar()
dropdown = tk.OptionMenu(top_bar, selected_conversation, "")
dropdown.pack(side=tk.LEFT, padx=5)

new_button = tk.Button(top_bar, text="New Chat", command=new_conversation)
new_button.pack(side=tk.LEFT, padx=5)

delete_button = tk.Button(top_bar, text="Delete Chat", command=delete_conversation)
delete_button.pack(side=tk.LEFT, padx=5)

# --- Chat window
chat_box = tk.Text(root)
chat_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# --- Spinner
spinner = ttk.Progressbar(root, mode="indeterminate")
spinner.pack(pady=5, padx=5, fill=tk.X)

# --- Input bar
bottom = tk.Frame(root)
bottom.pack(fill=tk.X, pady=5, padx=5)

entry = tk.Entry(bottom)
entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

send_button = tk.Button(bottom, text="Send", command=send_message)
send_button.pack(side=tk.LEFT, padx=5)

# -----------------------------
# INITIAL LOAD
# -----------------------------
refresh_dropdown()
conversations = get_conversations()
if conversations:
    select_conversation(conversations[0])

root.mainloop()