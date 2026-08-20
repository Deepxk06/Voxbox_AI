#!/usr/bin/env python3
"""
VoxBox API Client
Example script demonstrating how to use the VoxBox API with the FREE
Groq and Google Gemini providers.
"""

import requests
import json
import time
import sys
from typing import Optional

# Make console output encoding-safe (Windows cp1252 cannot print some unicode)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

class VoxBoxClient:
    def __init__(self, base_url: str = "http://localhost:5000", token: str = ""):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-VoxBox-Token"] = self.token
        return headers

    def models(self) -> dict:
        """List available providers and models."""
        try:
            response = self.session.get(f"{self.base_url}/api/models", headers=self._headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def chat(
        self,
        message: str,
        provider: str = "groq",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> dict:
        """
        Send a chat message to VoxBox

        Args:
            message: The user message
            provider: AI provider (groq, gemini)
            model: Specific model id (defaults to provider default)
            temperature: Response randomness (0.0-2.0)
            max_tokens: Maximum response length
            stream: Whether to stream the response

        Returns:
            Response dictionary with text and metadata
        """
        endpoint = "/api/chat/stream" if stream else "/api/chat"
        url = f"{self.base_url}{endpoint}"

        payload = {
            "provider": provider,
            "model": model,
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": message}]
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            if stream:
                return self._stream_request(url, payload)
            else:
                response = self.session.post(url, json=payload, headers=self._headers(), timeout=120)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    def _stream_request(self, url: str, payload: dict) -> dict:
        """Handle streaming responses"""
        response = self.session.post(url, json=payload, headers=self._headers(), stream=True, timeout=120)
        response.raise_for_status()

        full_text = ""
        start_time = time.time()

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                        if "token" in chunk:
                            full_text += chunk["token"]
                            print(chunk["token"], end="", flush=True)
                        elif "meta" in chunk:
                            elapsed = time.time() - start_time
                            return {
                                "text": full_text,
                                "meta": {
                                    **chunk["meta"],
                                    "actual_time": round(elapsed, 2)
                                }
                            }
                        elif "error" in chunk:
                            return {"error": chunk["error"]}
                    except json.JSONDecodeError:
                        pass

        print()  # New line after stream
        return {"text": full_text, "meta": {"provider": "unknown"}}

    def generate_title(self, message: str, provider: str = "groq", model: Optional[str] = None) -> str:
        """Generate a title for a conversation"""
        url = f"{self.base_url}/api/title"
        payload = {
            "provider": provider,
            "model": model,
            "message": message
        }

        try:
            response = self.session.post(url, json=payload, headers=self._headers(), timeout=30)
            response.raise_for_status()
            return response.json().get("title", "New Chat")
        except Exception as e:
            return "New Chat"


def demo_basic_chat():
    """Demo: Basic chat with all available providers"""
    print("=" * 60)
    print("VoxBox Demo - Basic Chat")
    print("=" * 60)

    client = VoxBoxClient()
    message = "Write a Python function to calculate factorial"

    print("\nAvailable providers:")
    print(json.dumps(client.models().get("providers", {}), indent=2))
    print("\n")

    for provider in ["groq", "gemini"]:
        print(f"\n{'=' * 60}")
        print(f"Testing with: {provider.upper()}")
        print(f"{'=' * 60}\n")

        try:
            result = client.chat(message, provider=provider, max_tokens=200)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Response:\n{result['text'][:300]}...")
                print(f"\nMetadata: {result.get('meta', {})}")
        except Exception as e:
            print(f"Exception: {e}")


def demo_streaming():
    """Demo: Streaming response"""
    print("\n" + "=" * 60)
    print("VoxBox Demo - Streaming")
    print("=" * 60 + "\n")

    client = VoxBoxClient()
    message = "Explain what is REST API in 100 words"

    print("Using Groq with streaming...")
    print("-" * 60)

    result = client.chat(message, provider="groq", stream=True, max_tokens=200)
    print(f"\n\nMetadata: {result.get('meta', {})}")


def demo_title_generation():
    """Demo: Title generation with different providers"""
    print("\n" + "=" * 60)
    print("VoxBox Demo - Title Generation")
    print("=" * 60 + "\n")

    client = VoxBoxClient()
    message = "How do I debug async code in JavaScript and what are the common pitfalls?"

    for provider in ["groq", "gemini"]:
        try:
            title = client.generate_title(message, provider=provider)
            print(f"{provider:10} -> {title}")
        except Exception as e:
            print(f"{provider:10} -> Error: {e}")


def demo_temperature_comparison():
    """Demo: Compare responses with different temperatures"""
    print("\n" + "=" * 60)
    print("VoxBox Demo - Temperature Comparison (Groq)")
    print("=" * 60 + "\n")

    client = VoxBoxClient()
    message = "What's an interesting fact about Python?"

    temperatures = [0.0, 0.7, 1.5]

    for temp in temperatures:
        print(f"\nTemperature: {temp}")
        print("-" * 40)

        result = client.chat(message, provider="groq", temperature=temp, max_tokens=100)

        if "error" not in result:
            print(f"Response: {result['text'][:150]}...")
        else:
            print(f"Error: {result['error']}")


def interactive_chat():
    """Interactive chat mode"""
    print("\n" + "=" * 60)
    print("VoxBox Interactive Chat")
    print("=" * 60)
    print("\nAvailable providers: groq, gemini")
    print("Commands:")
    print("  /provider <name>  - Switch provider (groq | gemini)")
    print("  /model <id>       - Switch model")
    print("  /quit             - Exit")
    print("  /stream           - Toggle streaming mode")
    print("=" * 60 + "\n")

    client = VoxBoxClient()
    current_provider = "groq"
    current_model = None
    stream_mode = False

    while True:
        try:
            user_input = input(f"[{current_provider}] You: ").strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                command = user_input.split()[0][1:]

                if command == "quit":
                    print("Goodbye!")
                    break
                elif command == "provider" and len(user_input.split()) > 1:
                    current_provider = user_input.split()[1].lower()
                    current_model = None
                    print(f"Switched to: {current_provider}")
                elif command == "model" and len(user_input.split()) > 1:
                    current_model = user_input.split()[1]
                    print(f"Model set to: {current_model}")
                elif command == "stream":
                    stream_mode = not stream_mode
                    print(f"Streaming: {'ON' if stream_mode else 'OFF'}")
                else:
                    print("Unknown command")
            else:
                print(f"\nAssistant: ", end="")
                result = client.chat(user_input, provider=current_provider, model=current_model, stream=stream_mode)

                if "error" not in result:
                    if not stream_mode:
                        print(result['text'])
                    print(f"\n[Tokens: {result.get('meta', {}).get('tokens', 'N/A')}, "
                          f"Time: {result.get('meta', {}).get('time', 'N/A')}s]")
                else:
                    print(f"Error: {result['error']}")
                print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "basic":
            demo_basic_chat()
        elif mode == "stream":
            demo_streaming()
        elif mode == "title":
            demo_title_generation()
        elif mode == "temp":
            demo_temperature_comparison()
        elif mode == "interactive":
            interactive_chat()
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: basic, stream, title, temp, interactive")
    else:
        print("VoxBox Client")
        print("=" * 60)
        print("\nUsage: python client.py <mode>\n")
        print("Available modes:")
        print("  basic       - Test all providers with a simple message")
        print("  stream      - Demo streaming response")
        print("  title       - Compare title generation across providers")
        print("  temp        - Compare temperature settings")
        print("  interactive - Interactive chat mode\n")
        print("Examples:")
        print("  python client.py basic")
        print("  python client.py interactive")
