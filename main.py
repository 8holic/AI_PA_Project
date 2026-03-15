import sqlite3
import os
import threading
import ollama
import tkinter as tk

from module_loader import load_modules
from app_core import App
from ui.main_window import MainWindow

# -----------------------------
# MODEL
# -----------------------------
model = "llama3:8b"

# -----------------------------
# SYSTEM PROMPT
# -----------------------------
prompt_file = os.path.join(os.path.dirname(__file__), "system_prompt.txt")

try:
    with open(prompt_file, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a helpful assistant."
print(SYSTEM_PROMPT)

# -----------------------------
# DATABASE
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

conversation_id = None
messages = []

app = App()
load_modules(app)

# -----------------------------
# AI FUNCTION
# -----------------------------
def ask_ai():
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    response = ollama.chat(
        model=model,
        messages=full_messages
    )
    return response["message"]["content"]

def get_conversations():
    cursor.execute("SELECT name FROM conversations")
    rows = cursor.fetchall()
    return [r[0] for r in rows]

def load_conversation(name):
    global conversation_id, messages

    cursor.execute("SELECT id FROM conversations WHERE name=?", (name,))
    row = cursor.fetchone()
    if not row:
        return False

    conversation_id = row[0]

    cursor.execute(
        "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id",
        (conversation_id,)
    )
    rows = cursor.fetchall()

    messages = []

    # include system prompt in messages but don't show in UI
    messages.append({"role": "system", "content": SYSTEM_PROMPT})

    # clear chat box and show user + assistant messages
    ui.clear_chat()
    for role, content in rows:
        messages.append({"role": role, "content": content})
        if role == "user":
            ui.chat_box.insert(tk.END, "You: " + content + "\n")
        else:
            ui.chat_box.insert(tk.END, "AI: " + content + "\n\n")
    ui.chat_box.see(tk.END)
    return True

def new_conversation():
    from tkinter import simpledialog, messagebox
    name = simpledialog.askstring("New Conversation", "Conversation name:")
    if not name:
        return
    cursor.execute("INSERT OR IGNORE INTO conversations (name) VALUES (?)", (name,))
    conn.commit()
    refresh_conversations()
    ui.select_conversation(name)
    load_conversation(name)

def delete_conversation(name):
    from tkinter import messagebox
    if not name:
        return
    confirm = messagebox.askyesno("Delete Conversation", f"Are you sure you want to delete '{name}'?")
    if not confirm:
        return
    cursor.execute("DELETE FROM messages WHERE conversation_id = (SELECT id FROM conversations WHERE name=?)", (name,))
    cursor.execute("DELETE FROM conversations WHERE name=?", (name,))
    conn.commit()
    refresh_conversations()
    # Clear chat if deleted conversation was current
    if ui.conv_listbox.curselection():
        selected_name = ui.conv_listbox.get(ui.conv_listbox.curselection()[0])
        if selected_name == name:
            ui.clear_chat()

def refresh_conversations():
    convs = get_conversations()
    ui.set_conversations(convs)
    # Optionally auto-select first conversation if none selected
    if convs and not ui.conv_listbox.curselection():
        ui.select_conversation(convs[0])
        load_conversation(convs[0])
    
# -----------------------------
# UI CALLBACKS
# -----------------------------
def send_message(user_text, ui):
    global messages

    # Disable user input while waiting
    ui.entry.config(state="disabled")
    ui.send_button.config(state="disabled")

    messages.append({"role": "user", "content": user_text})

    user_text = app.run_hook("before_send", user_text)

    def run():
        ai_text = ask_ai()

        messages.append({"role": "assistant", "content": ai_text})

        ai_text = app.run_hook("after_response", ai_text)

        def finish():
            ui.show_ai(ai_text)
            # Re-enable user input
            ui.entry.config(state="normal")
            ui.send_button.config(state="normal")
            # Optional: put focus back in the entry
            ui.entry.focus()

        ui.root.after(0, finish)

    threading.Thread(target=run).start()

# -----------------------------
# START UI
# -----------------------------
ui = MainWindow(send_message, {
    "on_select": lambda name: load_conversation(name),
    "on_new": new_conversation,
    "on_delete": delete_conversation,
})

refresh_conversations()  # populate the left panel
ui.run()