import os
import logging
import subprocess
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import deque
from datetime import datetime
 
# Configure logging
logger = logging.getLogger(__name__)
 
###############################################################################
# Sandbox Configuration
###############################################################################
 
WORKSPACE_DIR = Path(os.getenv('WORKSPACE_DIR', 'workspace')).resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'.py', '.txt', '.json', '.md', '.csv', '.log', '.pdf', '.html'}
 
def _sanitize_path(file_path: str) -> Path:
    target = (WORKSPACE_DIR / file_path).resolve()
    if not str(target).startswith(str(WORKSPACE_DIR)):
        raise ValueError(f"Operation denied: Path '{file_path}' is outside the allowed workspace.")
    if target.is_file() and target.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Operation denied: File extension '{target.suffix}' is not allowed.")
    return target
 
def sanitize_command(command: str) -> str:
    dangerous_keywords = ['rm', 'del', 'format', 'shutdown', 'mkfs', 'dd if=', ':">', ';>']
    command_lower = command.lower()
    for kw in dangerous_keywords:
        if kw in command_lower:
            raise ValueError(f"Blocked dangerous command: '{command}'. Contains forbidden keyword: '{kw}'")
    return command
 
###############################################################################
# ORPHEUS Agent Definitions
###############################################################################
 
class OrpheusAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.memory = deque(maxlen=100)
 
    def process(self, *args, **kwargs):
        raise NotImplementedError("Each agent must implement the process method.")
 
 
class CommanderAgent(OrpheusAgent):
    """The Router. Parses intent and delegates tasks."""
    def __init__(self):
        super().__init__("Commander", "Intent Router & Orchestrator")
 
    def process(self, command: str, voice_context: Dict = None) -> Dict:
        logger.info(f"CommanderAgent processing: '{command}'")
        self.memory.append({"role": "user", "content": command})
 
        command_lower = command.lower()
 
        if any(kw in command_lower for kw in ["read file", "write file", "create file", "run code", "execute", "list files", "delete file"]):
            intent = "file_os"
        elif any(kw in command_lower for kw in ["search", "look up", "find online", "research"]):
            intent = "web_research"
        elif any(kw in command_lower for kw in ["create quiz", "generate code", "make a", "build a", "write a document"]):
            intent = "creator"
        else:
            intent = "llm"
 
        result = {
            "status": "success",
            "intent": intent,
            "original_command": command,
            "target_agent": intent,
            "execution_context": voice_context
        }
        self.memory.append({"role": "system", "content": result})
        return result
 
 
class FileOSAgent(OrpheusAgent):
    """Handles secure access to the designated local directory."""
    def __init__(self):
        super().__init__("FileOS", "File & OS Operations Agent")
 
    def process(self, action: str, file_path: str, content: str = None) -> str:
        logger.info(f"FileOSAgent executing '{action}' on '{file_path}'")
        if action in ["write", "create"]:
            return self._write_file(file_path, content)
        elif action == "read":
            return self._read_file(file_path)
        elif action == "list":
            return self._list_files(file_path)
        elif action == "delete":
            return self._delete_file(file_path)
        elif action == "execute":
            return self._execute_file(file_path)
        else:
            return f"Error: Unknown action '{action}'"
 
    def _write_file(self, file_path: str, content: str) -> str:
        try:
            target = _sanitize_path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"
 
    def _read_file(self, file_path: str) -> str:
        try:
            target = _sanitize_path(file_path)
            with open(target, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
 
    def _list_files(self, directory: str = ".") -> str:
        try:
            target = _sanitize_path(directory)
            files = os.listdir(target)
            return "\n".join(files)
        except Exception as e:
            return f"Error listing files: {e}"
 
    def _delete_file(self, file_path: str) -> str:
        try:
            target = _sanitize_path(file_path)
            if target.is_dir():
                return "Error: Deleting directories is not allowed for safety."
            os.remove(target)
            return f"Successfully deleted {file_path}"
        except Exception as e:
            return f"Error deleting file: {e}"
 
    def _execute_file(self, file_path: str) -> str:
        try:
            target = _sanitize_path(file_path)
            if target.suffix != '.py':
                return "Error: Only .py files can be executed."
            result = subprocess.run(
                ['python', str(target)],
                capture_output=True,
                text=True,
                cwd=str(WORKSPACE_DIR),
                timeout=10
            )
            return f"Exit Code: {result.returncode}\nOutput:\n{result.stdout}\nErrors:\n{result.stderr}"
        except Exception as e:
            return f"Error executing file: {e}"
 
 
class WebResearchAgent(OrpheusAgent):
    """Connected to the internet via DuckDuckGo."""
    def __init__(self):
        super().__init__("WebResearch", "Internet Research Agent")
        try:
            from duckduckgo_search import DDGS
            self.ddg = DDGS()
        except ImportError:
            self.ddg = None
            logger.warning("duckduckgo_search not installed.")
 
    def process(self, query: str) -> str:
        logger.info(f"WebResearchAgent searching for: '{query}'")
        if not self.ddg:
            return "Error: DuckDuckGo search module is not installed."
        try:
            results = self.ddg.text(query, max_results=3)
            if results:
                summary = f"Here are the top results for '{query}':\n"
                for i, res in enumerate(results):
                    summary += f"{i+1}. [{res['title']}]({res['href']})\n{res['body']}\n\n"
                return summary
            else:
                return f"No results found for '{query}'."
        except Exception as e:
            return f"Error during web search: {e}"
 
 
class CreatorAgent(OrpheusAgent):
    """Generates structured payloads like JSON, documents, and code."""
    def __init__(self):
        super().__init__("Creator", "Content Creation Agent")
 
    def process(self, request: str, payload_type: str = "generic") -> str:
        logger.info(f"CreatorAgent generating '{payload_type}' content.")
        if "quiz" in request.lower():
            return self._generate_quiz(request)
        elif "code" in request.lower():
            return self._generate_code(request)
        else:
            return f"Creator Agent ready. Requested: {request}."
 
    def _generate_quiz(self, topic: str) -> str:
        quiz = {
            "topic": topic,
            "questions": [
                {"q": f"Sample question 1 about {topic}?", "a": "Answer 1"},
                {"q": f"Sample question 2 about {topic}?", "a": "Answer 2"}
            ]
        }
        FileOSAgent()._write_file("output_quiz.json", json.dumps(quiz, indent=2))
        return "Generated quiz and saved to output_quiz.json"
 
    def _generate_code(self, description: str) -> str:
        code = f"# AI Generated Code for: {description}\n\ndef main():\n    print('Hello from ORPHEUS Creator Agent')\n\nif __name__ == '__main__':\n    main()"
        FileOSAgent()._write_file("generated_code.py", code)
        return "Generated code and saved to generated_code.py"
 
 
class LLMAgent(OrpheusAgent):
    """Handles general conversation via Gemini / OpenAI / Ollama (fallback chain)."""

    SYSTEM_PROMPT = (
        "You are ORPHEUS, an advanced AI assistant — the Omni-Responsive Processing Matrix. "
        "You are intelligent, precise, and slightly futuristic in tone. "
        "You can reason through complex problems, write code, analyze data, explain concepts, "
        "and help with any task. Be concise but thorough. Use markdown formatting when helpful. "
        "You are running locally on the user's machine as their personal AI command center."
    )

    def __init__(self):
        super().__init__("LLM", "Conversational AI Agent")
        self.provider = os.getenv('LLM_PROVIDER', 'ollama').lower()
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '4096'))

        # Gemini config
        self.gemini_key = os.getenv('GEMINI_API_KEY', '')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

        # OpenAI config
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

        # Ollama config
        self.ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'tinyllama')

        logger.info(f"LLMAgent initialized — provider: {self.provider}")

    def process(self, command: str) -> str:
        """Process command through the configured LLM provider with fallback chain."""
        logger.info(f"LLMAgent [{self.provider}]: '{command[:80]}...'")

        # Build conversation with memory
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Add recent memory for context
        for mem in list(self.memory)[-6:]:
            if isinstance(mem.get("content"), str):
                messages.append(mem)

        messages.append({"role": "user", "content": command})

        # Try provider chain: configured → fallbacks
        providers = self._get_provider_chain()

        for provider_name in providers:
            try:
                result = self._call_provider(provider_name, messages, command)
                if result and not result.startswith("Error:"):
                    # Store in memory
                    self.memory.append({"role": "user", "content": command})
                    self.memory.append({"role": "assistant", "content": result[:500]})
                    return result
            except Exception as e:
                logger.warning(f"Provider '{provider_name}' failed: {e}")
                continue

        return (
            "All LLM providers failed. Please check:\n"
            "• Gemini: Set GEMINI_API_KEY in .env (free at https://aistudio.google.com/apikey)\n"
            "• OpenAI: Set OPENAI_API_KEY in .env\n"
            "• Ollama: Ensure Ollama is running at localhost:11434"
        )

    def _get_provider_chain(self) -> list:
        """Build ordered list of providers to try."""
        chain = [self.provider]
        all_providers = ['gemini', 'openai', 'ollama']
        for p in all_providers:
            if p not in chain:
                chain.append(p)
        return chain

    def _call_provider(self, provider: str, messages: list, raw_command: str) -> str:
        """Call a specific LLM provider."""
        if provider == 'gemini':
            return self._call_gemini(messages)
        elif provider == 'openai':
            return self._call_openai(messages)
        elif provider == 'ollama':
            return self._call_ollama(raw_command)
        else:
            return f"Error: Unknown provider '{provider}'"

    def _call_gemini(self, messages: list) -> str:
        """Call Google Gemini API using REST (no SDK dependency)."""
        if not self.gemini_key or self.gemini_key == 'PASTE_YOUR_GEMINI_KEY_HERE':
            raise ValueError("Gemini API key not configured")

        import requests

        # Build Gemini-format messages
        gemini_contents = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                gemini_contents.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
            elif msg["role"] == "assistant":
                gemini_contents.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })

        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent?key={self.gemini_key}"
        )

        response = requests.post(url, json=payload, timeout=60)

        if response.status_code != 200:
            error_detail = response.json().get("error", {}).get("message", response.text[:200])
            raise ValueError(f"Gemini API error ({response.status_code}): {error_detail}")

        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "No response text from Gemini.")

        return "Gemini returned an empty response."

    def _call_openai(self, messages: list) -> str:
        """Call OpenAI API using REST."""
        if not self.openai_key:
            raise ValueError("OpenAI API key not configured")

        import requests

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.openai_model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=60,
        )

        if response.status_code != 200:
            error_detail = response.json().get("error", {}).get("message", response.text[:200])
            raise ValueError(f"OpenAI API error ({response.status_code}): {error_detail}")

        data = response.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "No response from OpenAI.")

        return "OpenAI returned an empty response."

    def _call_ollama(self, command: str) -> str:
        """Call local Ollama instance."""
        import requests

        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.ollama_model,
                "prompt": f"{self.SYSTEM_PROMPT}\n\nUser: {command}\n\nAssistant:",
                "stream": False,
            },
            timeout=60,
        )

        data = response.json()
        return data.get("response", "No response from Ollama.")
 
 
###############################################################################
# Agent Harness (Orchestrator)
###############################################################################
 
class AgentHarness:
    def __init__(self):
        self.commander = CommanderAgent()
        self.file_agent = FileOSAgent()
        self.web_agent = WebResearchAgent()
        self.creator_agent = CreatorAgent()
        self.llm_agent = LLMAgent()
        self.agents = {
            "file_os": self.file_agent,
            "web_research": self.web_agent,
            "creator": self.creator_agent,
            "llm": self.llm_agent
        }
 
    def execute_command(self, command: str) -> str:
        routing = self.commander.process(command)
 
        if routing["status"] != "success":
            return "Command processing failed."
 
        target_agent_key = routing["target_agent"]
        agent = self.agents.get(target_agent_key)
 
        if not agent:
            return f"Agent '{target_agent_key}' not found."
 
        if isinstance(agent, FileOSAgent):
            if "read file" in command:
                parts = command.split("read file ")
                if len(parts) > 1:
                    return agent.process("read", parts[1].strip())
            elif "list files" in command:
                return agent.process("list", ".")
            else:
                return "FileOS command not recognized. Try 'read file <name>' or 'list files'."
 
        elif isinstance(agent, WebResearchAgent):
            return agent.process(command)
 
        elif isinstance(agent, CreatorAgent):
            return agent.process(command)
 
        elif isinstance(agent, LLMAgent):
            return agent.process(command)
 
        return "Execution complete."
 