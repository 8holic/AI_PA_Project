import tkinter as tk
from tkinter import ttk
from .style import apply_styles


class MainWindow:

    def __init__(self, send_callback, conversation_callbacks):
        """
        conversation_callbacks: dict with keys:
          - on_select(name)
          - on_new()
          - on_delete(name)
        """
        self.root = tk.Tk()
        self.root.title("Local Assistant")
        self.root.geometry("1000x650")

        # Apply styles
        colors = apply_styles(self.root)
        bg = colors["bg"]
        panel = colors["panel"]
        text = colors["text"]

        self.send_callback = send_callback
        self.conversation_callbacks = conversation_callbacks

        # Main container
        main_frame = ttk.Frame(self.root, style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # -----------------------------
        # Left panel for conversations
        # -----------------------------
        left_panel = ttk.Frame(main_frame, style="Panel.TFrame", width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.conv_listbox = tk.Listbox(
            left_panel,
            bg=panel,
            fg=text,
            font=("Segoe UI", 11),
            selectmode=tk.SINGLE,
            activestyle='none',
            highlightthickness=0,
            relief="flat",
        )
        self.conv_listbox.pack(fill=tk.BOTH, expand=True)
        self.conv_listbox.bind("<<ListboxSelect>>", self._on_conv_select)

        btn_frame = ttk.Frame(left_panel, style="Panel.TFrame")
        btn_frame.pack(fill=tk.X, pady=(10,0))

        self.new_conv_button = ttk.Button(btn_frame, text="New Chat", style="Purple.TButton", command=self._on_new_conv)
        self.new_conv_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.delete_conv_button = ttk.Button(btn_frame, text="Delete Chat", style="Purple.TButton", command=self._on_delete_conv)
        self.delete_conv_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # -----------------------------
        # Right panel for chat and input
        # -----------------------------
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        chat_container = tk.Frame(right_panel, bg=panel)
        chat_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.chat_box = tk.Text(
            chat_container,
            bg=panel,
            fg=text,
            insertbackground=text,
            relief="flat",
            wrap="word",
            font=("Segoe UI", 11),
            padx=10,
            pady=10
        )
        scrollbar = ttk.Scrollbar(chat_container, command=self.chat_box.yview)
        self.chat_box.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Spinner
        self.spinner = ttk.Progressbar(
            right_panel,
            mode="indeterminate",
            style="Purple.Horizontal.TProgressbar"
        )
        self.spinner.pack(fill=tk.X, padx=15)

        # Bottom input bar
        bottom_frame = ttk.Frame(right_panel, style="Panel.TFrame")
        bottom_frame.pack(fill=tk.X, padx=15, pady=15)

        self.entry = ttk.Entry(bottom_frame, style="Purple.TEntry", font=("Segoe UI", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.send_button = ttk.Button(bottom_frame, text="Send", style="Purple.TButton", command=self.send)
        self.send_button.pack(side=tk.RIGHT)

        self.entry.bind("<Return>", lambda event: self.send())

    # -----------------------------
    # Conversation Listbox handlers
    # -----------------------------
    def _on_conv_select(self, event):
        selection = self.conv_listbox.curselection()
        if not selection:
            return
        name = self.conv_listbox.get(selection[0])
        if self.conversation_callbacks.get("on_select"):
            self.conversation_callbacks["on_select"](name)

    def _on_new_conv(self):
        if self.conversation_callbacks.get("on_new"):
            self.conversation_callbacks["on_new"]()

    def _on_delete_conv(self):
        selection = self.conv_listbox.curselection()
        if not selection:
            return
        name = self.conv_listbox.get(selection[0])
        if self.conversation_callbacks.get("on_delete"):
            self.conversation_callbacks["on_delete"](name)

    # -----------------------------
    # Public API for conversations
    # -----------------------------
    def set_conversations(self, conv_names):
        self.conv_listbox.delete(0, tk.END)
        for c in conv_names:
            self.conv_listbox.insert(tk.END, c)

    def select_conversation(self, name):
        names = self.conv_listbox.get(0, tk.END)
        if name in names:
            idx = names.index(name)
            self.conv_listbox.select_clear(0, tk.END)
            self.conv_listbox.select_set(idx)
            self.conv_listbox.see(idx)

    # -----------------------------
    # Chat and input
    # -----------------------------
    def send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.chat_box.insert(tk.END, "You: " + text + "\n")
        self.chat_box.see(tk.END)
        self.spinner.start()
        self.send_callback(text, self)

    def show_ai(self, text):
        self.spinner.stop()
        self.chat_box.insert(tk.END, "AI: " + text + "\n\n")
        self.chat_box.see(tk.END)

    def clear_chat(self):
        self.chat_box.delete("1.0", tk.END)

    def run(self):
        self.root.mainloop()