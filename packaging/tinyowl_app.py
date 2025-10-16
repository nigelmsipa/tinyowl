#!/usr/bin/env python3
"""
TinyOwl - Theological AI Assistant
Simple desktop application with embedded fine-tuned model
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import os
import sys
from llama_cpp import Llama

class TinyOwlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TinyOwl - Theological AI Assistant")
        self.root.geometry("800x600")

        # Model path (relative to app)
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(__file__)

        self.model_path = os.path.join(base_path, "models", "tinyowl-q4.gguf")
        self.llm = None
        self.loading = False

        self.setup_ui()

        # Load model in background
        threading.Thread(target=self.load_model, daemon=True).start()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(header, text="🦉 TinyOwl",
                        font=("Arial", 20, "bold"),
                        bg="#2c3e50", fg="white")
        title.pack(pady=10)

        subtitle = tk.Label(header, text="Your Personal Theological Assistant",
                           font=("Arial", 10),
                           bg="#2c3e50", fg="#ecf0f1")
        subtitle.pack()

        # Chat display
        chat_frame = tk.Frame(self.root, bg="white")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#2c3e50",
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Configure tags for styling
        self.chat_display.tag_config("user", foreground="#27ae60", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("assistant", foreground="#2980b9", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("system", foreground="#95a5a6", font=("Arial", 10, "italic"))

        # Input area
        input_frame = tk.Frame(self.root, bg="white")
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.input_field = tk.Entry(input_frame, font=("Arial", 12))
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", lambda e: self.send_message())

        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)
        self.send_button.config(state=tk.DISABLED)

        # Status bar
        self.status_bar = tk.Label(self.root, text="Loading model...",
                                   bg="#34495e", fg="white",
                                   font=("Arial", 9), anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Welcome message
        self.add_message("system", "Welcome to TinyOwl! Loading model, please wait...")

    def load_model(self):
        try:
            self.loading = True
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
            self.root.after(0, self.model_loaded)
        except Exception as e:
            self.root.after(0, lambda: self.model_error(str(e)))

    def model_loaded(self):
        self.loading = False
        self.send_button.config(state=tk.NORMAL)
        self.status_bar.config(text="Ready - TinyOwl model loaded ✓")
        self.add_message("system", "TinyOwl is ready! Ask me theological questions.")
        self.input_field.focus()

    def model_error(self, error):
        self.loading = False
        self.status_bar.config(text=f"Error loading model: {error}")
        self.add_message("system", f"Failed to load model: {error}")

    def add_message(self, role, text):
        self.chat_display.config(state=tk.NORMAL)

        if role == "user":
            self.chat_display.insert(tk.END, "You: ", "user")
        elif role == "assistant":
            self.chat_display.insert(tk.END, "TinyOwl: ", "assistant")
        elif role == "system":
            self.chat_display.insert(tk.END, "• ", "system")

        self.chat_display.insert(tk.END, text + "\n\n", role if role == "system" else "")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def send_message(self):
        if self.loading or not self.llm:
            return

        user_input = self.input_field.get().strip()
        if not user_input:
            return

        self.input_field.delete(0, tk.END)
        self.add_message("user", user_input)
        self.send_button.config(state=tk.DISABLED)
        self.status_bar.config(text="Thinking...")

        # Generate response in background
        threading.Thread(target=self.generate_response, args=(user_input,), daemon=True).start()

    def generate_response(self, question):
        try:
            response = self.llm.create_chat_completion(
                messages=[{"role": "user", "content": question}],
                max_tokens=300,
                temperature=0.7,
            )
            answer = response['choices'][0]['message']['content']
            self.root.after(0, lambda: self.display_response(answer))
        except Exception as e:
            self.root.after(0, lambda: self.display_error(str(e)))

    def display_response(self, text):
        self.add_message("assistant", text)
        self.send_button.config(state=tk.NORMAL)
        self.status_bar.config(text="Ready")
        self.input_field.focus()

    def display_error(self, error):
        self.add_message("system", f"Error: {error}")
        self.send_button.config(state=tk.NORMAL)
        self.status_bar.config(text="Ready")

def main():
    root = tk.Tk()
    app = TinyOwlApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
