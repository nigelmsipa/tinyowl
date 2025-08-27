#!/usr/bin/env python3
"""
TinyOwl Interactive Chat Interface
Beautiful terminal chat with model switching, RAG toggle, and loading animations
"""

import sys
import time
import json
import random
import threading
import requests
import chromadb
from datetime import datetime
import os
import textwrap
import shutil

# Terminal colors and styling
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m' 
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'

# Fun loading words like Claude
THINKING_WORDS = [
    "philosophizing", "contemplating", "pondering", "ruminating", "reflecting",
    "deliberating", "cogitating", "meditating", "theorizing", "analyzing",
    "synthesizing", "reasoning", "deducing", "inferring", "evaluating",
    "interpreting", "examining", "exploring", "investigating", "discovering",
    "unraveling", "deciphering", "illuminating", "clarifying", "elucidating",
    "channeling ancient wisdom", "consulting sacred texts", "diving deep",
    "connecting the dots", "weaving insights", "parsing scripture",
    "seeking truth", "gathering wisdom", "harmonizing thoughts"
]

class LoadingSpinner:
    """Animated loading spinner with random thinking words"""
    
    def __init__(self):
        self.spinning = False
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_word = ""
        
    def start(self, custom_word=None):
        self.spinning = True
        self.current_word = custom_word or random.choice(THINKING_WORDS)
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        self.spinning = False
        if hasattr(self, 'thread'):
            self.thread.join()
        # Clear the line with dynamic width
        terminal_width = 80
        try:
            terminal_width = shutil.get_terminal_size().columns
        except:
            pass
        print(f"\r{' ' * terminal_width}\r", end='', flush=True)
    
    def _spin(self):
        i = 0
        while self.spinning:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            # Align spinner with the rest of the content (2-space indent)
            print(f"\r  {Colors.OKCYAN}{char} {self.current_word}...{Colors.ENDC}", end='', flush=True)
            time.sleep(0.1)
            i += 1

class TinyOwlChat:
    """Interactive chat interface for TinyOwl"""
    
    def __init__(self):
        self.spinner = LoadingSpinner()
        self.rag_enabled = True
        self.current_model = "qwen2.5-coder:3b"  # Best performing model from tests
        self.available_models = []
        self.collection = None
        self.history = []
        
        # Get terminal dimensions for responsive design
        self.terminal_width = self.get_terminal_width()
        self.content_width = max(40, self.terminal_width - 8)  # Leave 4 chars padding each side
        self.text_width = max(35, self.content_width - 8)      # Leave more space for text wrapping, min 35
        
        self.print_header()
        self.initialize_system()
    
    def get_terminal_width(self):
        """Get current terminal width, fallback to reasonable default"""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80  # Fallback for tiling managers or when detection fails
    
    def print_header(self):
        """Print fancy header with responsive width"""
        print()
        separator = '=' * self.content_width
        print(f"  {Colors.HEADER}{separator}{Colors.ENDC}")
        
        # Center the title if width allows
        title = "🦉 TinyOwl Interactive Chat"
        if len(title) < self.content_width - 4:
            padding = (self.content_width - len(title)) // 2
            centered_title = ' ' * padding + title
        else:
            centered_title = title
        
        print(f"  {Colors.HEADER}{Colors.BOLD}{centered_title}{Colors.ENDC}")
        
        # Center subtitle
        subtitle = "Your personal theological knowledge assistant"
        if len(subtitle) < self.content_width - 4:
            padding = (self.content_width - len(subtitle)) // 2
            centered_subtitle = ' ' * padding + subtitle
        else:
            centered_subtitle = subtitle
            
        print(f"  {Colors.DIM}{centered_subtitle}{Colors.ENDC}")
        print(f"  {Colors.HEADER}{separator}{Colors.ENDC}")
        print()
        print()
    
    def initialize_system(self):
        """Initialize RAG database and check available models"""
        self.spinner.start("initializing knowledge base")
        
        try:
            # Connect to ChromaDB
            client = chromadb.PersistentClient(path="vectordb")
            self.collection = client.get_collection("theology")
            doc_count = self.collection.count()
            
            self.spinner.stop()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Connected to theology database ({doc_count} documents)")
            
        except Exception as e:
            self.spinner.stop()
            print(f"  {Colors.FAIL}✗ Failed to connect to database: {e}{Colors.ENDC}")
            sys.exit(1)
        
        # Check available models
        self.spinner.start("scanning available models")
        self.check_available_models()
        self.spinner.stop()
        
        if self.available_models:
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Found {len(self.available_models)} available models")
        else:
            print(f"  {Colors.WARNING}⚠ No models available. Make sure Ollama is running.{Colors.ENDC}")
            sys.exit(1)
        
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} System ready!")
        print()
        print()
        self.print_status()
        self.print_help()
    
    def check_available_models(self):
        """Check which models are available in Ollama"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model["name"] for model in models_data.get("models", [])]
                
                # Set current model to first available if current isn't available
                if self.current_model not in self.available_models and self.available_models:
                    self.current_model = self.available_models[0]
            
        except Exception as e:
            print(f"{Colors.WARNING}Could not check models: {e}{Colors.ENDC}")
    
    def print_status(self):
        """Print current system status with proper spacing"""
        rag_status = f"{Colors.OKGREEN}ON{Colors.ENDC}" if self.rag_enabled else f"{Colors.WARNING}OFF{Colors.ENDC}"
        print(f"  {Colors.BOLD}Status:{Colors.ENDC}")
        print(f"    🤖 Model: {Colors.OKCYAN}{self.current_model}{Colors.ENDC}")
        print(f"    📚 RAG: {rag_status}")
        print(f"    💬 History: {len(self.history)} messages")
        print()
    
    def print_help(self):
        """Print available commands with responsive layout"""
        print(f"  {Colors.BOLD}Commands:{Colors.ENDC}")
        
        # For very narrow terminals, use compact format
        if self.terminal_width < 60:
            commands = [
                ("/models", "List models"),
                ("/switch", "Switch model"), 
                ("/rag", "Toggle RAG"),
                ("/status", "Show status"),
                ("/clear", "Clear history"),
                ("/help", "Show help"),
                ("/quit", "Exit")
            ]
            for cmd, desc in commands:
                print(f"    {Colors.OKCYAN}{cmd:<8}{Colors.ENDC} - {desc}")
        else:
            # Standard format for wider terminals
            print(f"    {Colors.OKCYAN}/models{Colors.ENDC}    - List available models")
            print(f"    {Colors.OKCYAN}/switch{Colors.ENDC}     - Switch model")
            print(f"    {Colors.OKCYAN}/rag{Colors.ENDC}        - Toggle RAG on/off")
            print(f"    {Colors.OKCYAN}/status{Colors.ENDC}     - Show current status")
            print(f"    {Colors.OKCYAN}/clear{Colors.ENDC}      - Clear chat history")
            print(f"    {Colors.OKCYAN}/help{Colors.ENDC}       - Show this help")
            print(f"    {Colors.OKCYAN}/quit{Colors.ENDC}       - Exit chat")
        
        print()
        print()
    
    def get_context(self, query, n_results=3):
        """Get context from RAG database"""
        if not self.rag_enabled or not self.collection:
            return ""
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results["documents"][0]:
                return ""
            
            # Format context
            context_parts = []
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                title = metadata.get("title", "Unknown")
                author = metadata.get("author", "")
                
                # Limit context to prevent token overflow
                short_doc = doc[:300] + "..." if len(doc) > 300 else doc
                
                source_info = f"{title}"
                if author:
                    source_info += f" by {author}"
                
                context_parts.append(f"[{source_info}]: {short_doc}")
            
            return "\\n\\n".join(context_parts)
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠ RAG retrieval error: {e}{Colors.ENDC}")
            return ""
    
    def query_llm(self, prompt):
        """Query the current LLM model"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 300
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated").strip()
            else:
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error: {e}"
    
    def process_query(self, query):
        """Process a user query"""
        self.history.append({"role": "user", "content": query, "timestamp": datetime.now()})
        
        # Build prompt
        if self.rag_enabled:
            self.spinner.start("searching knowledge base")
            context = self.get_context(query)
            self.spinner.stop()
            
            if context:
                prompt = f"""Based on the following information from religious texts, please provide a helpful and accurate response.

Context from knowledge base:
{context}

Question: {query}

Please answer based on the provided context. If the context doesn't fully answer the question, say so and provide what information you can."""
            else:
                prompt = f"""I couldn't find specific information in my knowledge base about: {query}

Please provide a general response based on your training, but note that I don't have specific source material for this topic."""
        else:
            prompt = f"""Please respond to this question: {query}

Note: RAG (knowledge base search) is currently disabled, so I'm responding based on general knowledge only."""
        
        # Get LLM response
        thinking_word = random.choice(THINKING_WORDS)
        self.spinner.start(thinking_word)
        
        response = self.query_llm(prompt)
        
        self.spinner.stop()
        
        self.history.append({"role": "assistant", "content": response, "timestamp": datetime.now()})
        
        return response
    
    def handle_command(self, command):
        """Handle special commands"""
        if command == "/models":
            print()
            print(f"  {Colors.BOLD}Available Models:{Colors.ENDC}")
            print()
            for i, model in enumerate(self.available_models):
                marker = f"{Colors.OKGREEN}→{Colors.ENDC}" if model == self.current_model else " "
                # Truncate model names for narrow terminals
                display_model = model
                if self.terminal_width < 60 and len(model) > 25:
                    display_model = model[:22] + "..."
                print(f"    {marker} {i+1}. {display_model}")
            print()
            print()
            
        elif command == "/switch":
            print()
            print(f"  {Colors.BOLD}Switch Model:{Colors.ENDC}")
            print()
            for i, model in enumerate(self.available_models):
                marker = f"{Colors.OKGREEN}*{Colors.ENDC}" if model == self.current_model else " "
                print(f"    {marker} {i+1}. {model}")
            
            try:
                print()
                choice = input(f"    Enter model number (1-{len(self.available_models)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(self.available_models):
                    self.current_model = self.available_models[idx]
                    print(f"    {Colors.OKGREEN}✓ Switched to {self.current_model}{Colors.ENDC}")
                else:
                    print(f"    {Colors.FAIL}Invalid selection{Colors.ENDC}")
            except (ValueError, KeyboardInterrupt):
                print(f"    {Colors.WARNING}Cancelled{Colors.ENDC}")
            print()
            print()
            
        elif command == "/rag":
            self.rag_enabled = not self.rag_enabled
            status = f"{Colors.OKGREEN}enabled{Colors.ENDC}" if self.rag_enabled else f"{Colors.WARNING}disabled{Colors.ENDC}"
            print()
            print(f"  📚 RAG is now {status}")
            print()
            print()
            
        elif command == "/status":
            self.print_status()
            
        elif command == "/clear":
            self.history = []
            os.system('clear' if os.name == 'posix' else 'cls')
            self.print_header()
            print(f"  {Colors.OKGREEN}✓ History cleared{Colors.ENDC}")
            print()
            print()
            
        elif command == "/help":
            self.print_help()
            
        elif command == "/quit":
            print()
            print(f"  {Colors.OKCYAN}👋 Goodbye!{Colors.ENDC}")
            print()
            return False
            
        else:
            print()
            print(f"  {Colors.WARNING}Unknown command: {command}{Colors.ENDC}")
            print(f"  Type /help for available commands")
            print()
            print()
        
        return True
    
    def run(self):
        """Main chat loop"""
        print(f"  {Colors.DIM}Ready to chat! Ask me anything about theology or type /help for commands.{Colors.ENDC}")
        print()
        print()
        
        while True:
            try:
                # Get user input with proper spacing
                user_input = input(f"  {Colors.BOLD}You:{Colors.ENDC} ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if not self.handle_command(user_input):
                        break
                    continue
                
                # Process query
                response = self.process_query(user_input)
                
                # Display response with proper spacing and indentation
                print()
                print(f"  {Colors.BOLD}🦉 TinyOwl:{Colors.ENDC}")
                print()
                
                # Format response with proper indentation
                try:
                    # Word wrap the response with responsive width and ensure indentation
                    wrapped_response = textwrap.fill(response, 
                                                   width=max(30, self.text_width), 
                                                   initial_indent="    ", 
                                                   subsequent_indent="    ",
                                                   break_long_words=False,
                                                   break_on_hyphens=False)
                    print(wrapped_response)
                except Exception as e:
                    # Fallback: manually add indentation to each line
                    lines = response.split('\n')
                    for line in lines:
                        if len(line.strip()) > 0:
                            print(f"    {line}")
                        else:
                            print()
                
                print()
                print()
                
            except KeyboardInterrupt:
                print(f"\n\n  {Colors.OKCYAN}👋 Goodbye!{Colors.ENDC}\n")
                break
            except Exception as e:
                print()
                print(f"  {Colors.FAIL}Error: {e}{Colors.ENDC}")
                print()
                print()

def main():
    chat = TinyOwlChat()
    chat.run()

if __name__ == "__main__":
    main()