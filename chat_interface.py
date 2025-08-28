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
from groq import Groq

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
        self.api_models = ["groq:llama-3.1-70b-versatile", "groq:llama-3.1-8b-instant", "groq:mixtral-8x7b-32768"]
        self.collection = None
        self.history = []  # Temporary session memory - cleared when chat ends
        self.session_id = int(time.time())  # Simple session identifier
        
        # API clients
        self.groq_client = None
        self.setup_api_clients()
        
        # Get terminal dimensions for responsive design
        self.terminal_width = self.get_terminal_width()
        self.content_width = max(40, self.terminal_width - 8)  # Leave 4 chars padding each side
        self.text_width = max(35, self.content_width - 8)      # Leave more space for text wrapping, min 35
        
        self.print_header()
        self.initialize_system()
    
    def setup_api_clients(self):
        """Setup API clients if keys are available"""
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
                print(f"  {Colors.OKGREEN}✓ Groq API connected{Colors.ENDC}")
            except:
                print(f"  {Colors.WARNING}⚠ Groq API key found but connection failed{Colors.ENDC}")
        else:
            print(f"  {Colors.DIM}• Set GROQ_API_KEY environment variable to use Groq models{Colors.ENDC}")

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
        """Check which models are available (Ollama + API)"""
        # Check Ollama models
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model["name"] for model in models_data.get("models", [])]
        except Exception as e:
            print(f"{Colors.WARNING}Could not check Ollama models: {e}{Colors.ENDC}")
            self.available_models = []
        
        # Add API models if clients are available
        if self.groq_client:
            self.available_models.extend(self.api_models)
        
        # Set current model to first available if current isn't available
        if self.current_model not in self.available_models and self.available_models:
            self.current_model = self.available_models[0]
    
    def print_status(self):
        """Print current system status with proper spacing"""
        rag_status = f"{Colors.OKGREEN}ON{Colors.ENDC}" if self.rag_enabled else f"{Colors.WARNING}OFF{Colors.ENDC}"
        context_status = f"{Colors.OKGREEN}Session memory{Colors.ENDC}" if len(self.history) > 0 else f"{Colors.DIM}No context yet{Colors.ENDC}"
        print(f"  {Colors.BOLD}Status:{Colors.ENDC}")
        print(f"    🤖 Model: {Colors.OKCYAN}{self.current_model}{Colors.ENDC}")
        print(f"    📚 RAG: {rag_status}")
        print(f"    💬 Context: {context_status} ({len(self.history)} messages)")
        print(f"    🔄 Session: Temporary (cleared on exit)")
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
        """Query the current LLM model (Ollama or API)"""
        try:
            # Handle Groq API models
            if self.current_model.startswith("groq:"):
                if not self.groq_client:
                    return "Error: Groq API not available"
                
                model_name = self.current_model.replace("groq:", "")
                response = self.groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
            
            # Handle local Ollama models
            else:
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
    
    def detect_topic_change(self, current_query):
        """Detect if the current query represents a topic change"""
        if not self.history or len(self.history) < 2:
            return False
        
        # Get recent user questions (excluding current one)
        recent_user_messages = [entry["content"] for entry in self.history[:-1] if entry["role"] == "user"]
        if not recent_user_messages:
            return False
        
        last_query = recent_user_messages[-1].lower()
        current_query_lower = current_query.lower()
        
        # Topic change indicators
        topic_change_phrases = [
            "let's talk about", "now about", "switching to", "new topic", 
            "different question", "change subject", "another thing",
            "moving on", "next question", "what about", "how about"
        ]
        
        # Strong indicators of topic change
        if any(phrase in current_query_lower for phrase in topic_change_phrases):
            return True
        
        # Simple keyword overlap check
        def extract_keywords(text):
            # Remove common words and get meaningful keywords
            common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "what", "how", "why", "when", "where", "who", "does", "do", "did", "can", "could", "would", "should", "will"}
            words = set(word.strip(".,!?;:\"'()") for word in text.lower().split())
            return words - common_words
        
        last_keywords = extract_keywords(last_query)
        current_keywords = extract_keywords(current_query_lower)
        
        if not last_keywords or not current_keywords:
            return False
        
        # Calculate keyword overlap
        overlap = len(last_keywords.intersection(current_keywords))
        similarity = overlap / max(len(last_keywords), len(current_keywords))
        
        # If similarity is very low (< 20%), likely a topic change
        return similarity < 0.2

    def get_conversation_context(self, max_turns=3):
        """Get recent conversation history for context"""
        if not self.history:
            return "Conversation context: This is the start of our conversation."
        
        # Check if current query is a topic change
        current_query = self.history[-1]["content"]
        if self.detect_topic_change(current_query):
            return "Conversation context: Starting fresh on a new topic."  # Clear context for topic changes
        
        # Get last max_turns exchanges (user + assistant pairs)
        recent_history = self.history[-max_turns*2:] if len(self.history) > max_turns*2 else self.history[:-1]  # Exclude current user message
        
        if not recent_history:
            return "Conversation context: This is the start of our conversation."
        
        context_lines = ["Recent conversation context:"]
        for entry in recent_history:
            role = "You" if entry["role"] == "user" else "TinyOwl"
            # Truncate long messages for context
            content = entry["content"][:150] + "..." if len(entry["content"]) > 150 else entry["content"]
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def build_contextual_query(self, query):
        """Build a context-aware query for better RAG retrieval"""
        if not self.history or len(self.history) < 2:
            return query
        
        # Check if this is a topic change - if so, don't add context
        if self.detect_topic_change(query):
            return query
        
        # Get recent user questions to understand the conversation thread
        recent_user_messages = [entry["content"] for entry in self.history[-6:] if entry["role"] == "user"]
        
        if len(recent_user_messages) <= 1:
            return query
        
        # If the current query seems to be a follow-up (contains words like "that", "this", "it", etc.)
        follow_up_indicators = ["that", "this", "it", "they", "them", "which", "what about", "how about", "and", "also", "too", "as well"]
        
        query_lower = query.lower()
        is_follow_up = any(indicator in query_lower for indicator in follow_up_indicators)
        
        if is_follow_up and len(recent_user_messages) > 1:
            # Combine recent context with current query for better retrieval
            previous_topics = " ".join(recent_user_messages[-3:-1])  # Last 2 questions before current
            contextual_query = f"{previous_topics} {query}"
            return contextual_query
        
        return query
    
    def process_query(self, query):
        """Process a user query with conversation context"""
        self.history.append({"role": "user", "content": query, "timestamp": datetime.now()})
        
        # Build context-aware query for better RAG retrieval
        contextual_query = self.build_contextual_query(query)
        
        # Build prompt
        if self.rag_enabled:
            self.spinner.start("searching knowledge base")
            context = self.get_context(contextual_query)
            self.spinner.stop()
            
            # Get recent conversation history for context
            conversation_context = self.get_conversation_context()
            
            if context:
                prompt = f"""You are TinyOwl, a knowledgeable theological assistant. Based on the conversation history and information from religious texts, provide a helpful and accurate response.

{conversation_context}

Context from knowledge base:
{context}

Current question: {query}

Please provide a thoughtful response that:
1. Considers the ongoing conversation context
2. Uses the provided religious text context
3. Maintains continuity with previous discussion
4. If this relates to something discussed before, acknowledge that connection"""

            else:
                prompt = f"""You are TinyOwl, a theological assistant. I couldn't find specific information in the knowledge base for this query.

{conversation_context}

Current question: {query}

Please provide a helpful response based on the conversation context and general theological knowledge, noting that specific source material wasn't found."""
        else:
            conversation_context = self.get_conversation_context()
            prompt = f"""You are TinyOwl, a theological assistant. RAG search is currently disabled.

{conversation_context}

Current question: {query}

Please respond based on the conversation context and general knowledge."""
        
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
        print(f"  {Colors.DIM}Ready to chat! I'll remember our conversation context during this session.{Colors.ENDC}")
        print(f"  {Colors.DIM}Ask me anything about theology or type /help for commands.{Colors.ENDC}")
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