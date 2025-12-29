#!/usr/bin/env python
"""
CLI Test Interface for z3-Agent
Interactive terminal-based testing for Telegram/Instagram agent responses.

Usage:
    python test_agent_cli.py
    python test_agent_cli.py --channel telegram
    python test_agent_cli.py --channel instagram
    python test_agent_cli.py --debug
"""

import sys
import argparse
from typing import Literal
from datetime import datetime

# Import z3-Agent core components
from app.core.router import supervisor_route
from app.core.rag import retrieve_context
from app.core.reply import generate_telegram_reply, generate_reply


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class AgentTester:
    """Interactive CLI tester for z3-Agent"""

    def __init__(self, channel: Literal["telegram", "instagram"] = "telegram", debug: bool = False):
        self.channel = channel
        self.debug = debug
        self.conversation_history = []

        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("=" * 70)
        print("  z3-Agent CLI Test Interface")
        print(f"  Channel: {channel.upper()}")
        print(f"  Debug Mode: {'ON' if debug else 'OFF'}")
        print("=" * 70)
        print(f"{Colors.END}")

    def print_separator(self):
        print(f"{Colors.CYAN}{'─' * 70}{Colors.END}")

    def print_debug(self, label: str, content: str):
        if self.debug:
            print(f"{Colors.YELLOW}[DEBUG] {label}:{Colors.END}")
            print(f"{Colors.YELLOW}{content}{Colors.END}")
            print()

    def process_message(self, user_message: str, username: str = "test_user") -> dict:
        """Process a user message through the agent pipeline"""

        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\n{Colors.CYAN}[{timestamp}] Processing message...{Colors.END}")
        self.print_separator()

        # Generate mock IDs for testing
        post_id = f"post_{len(self.conversation_history)}"
        comment_id = f"comment_{len(self.conversation_history)}"
        chat_id = f"chat_{len(self.conversation_history)}"

        # Step 1: Routing Decision
        print(f"{Colors.BLUE}Step 1: Supervisor Routing{Colors.END}")
        routing_mode = supervisor_route(user_input=user_message, history_context="")
        print(f"  → Routing Mode: {Colors.BOLD}{routing_mode.upper()}{Colors.END}")
        self.print_debug("Routing Decision", f"Mode: {routing_mode}")

        # Step 2: Context Retrieval (if needed)
        context = ""
        if routing_mode in {"docs", "web", "all"}:
            print(f"\n{Colors.BLUE}Step 2: RAG Context Retrieval{Colors.END}")
            print(f"  → Retrieving from: {routing_mode}")
            context = retrieve_context(user_message, mode=routing_mode)

            if context:
                context_preview = context[:200] + "..." if len(context) > 200 else context
                print(f"  → Context retrieved: {len(context)} chars")
                self.print_debug("Retrieved Context", context_preview)
            else:
                print(f"  → {Colors.YELLOW}No context found{Colors.END}")
        else:
            print(f"\n{Colors.BLUE}Step 2: RAG Context Retrieval{Colors.END}")
            print(f"  → {Colors.YELLOW}Skipped (direct mode){Colors.END}")

        # Step 3: Reply Generation
        print(f"\n{Colors.BLUE}Step 3: Reply Generation{Colors.END}")

        if self.channel == "telegram":
            reply = generate_telegram_reply(
                comment=user_message,
                context=context,
                history_context=""  # Could be enhanced with actual history
            )
        else:  # Instagram
            reply = generate_reply(
                comment=user_message,
                post_id=post_id,
                comment_id=comment_id,
                username=username,
                context=context
            )

        print(f"  → Reply generated: {len(reply)} chars")

        # Store in history
        interaction = {
            "timestamp": timestamp,
            "user": user_message,
            "routing": routing_mode,
            "context_length": len(context),
            "reply": reply
        }
        self.conversation_history.append(interaction)

        return interaction

    def display_response(self, interaction: dict, username: str):
        """Display the agent response in a nice format"""
        self.print_separator()
        print(f"{Colors.GREEN}{Colors.BOLD}Agent Response:{Colors.END}")
        print(f"{Colors.GREEN}{interaction['reply']}{Colors.END}")
        self.print_separator()

        # Show metadata
        print(f"{Colors.CYAN}Metadata:{Colors.END}")
        print(f"  Routing: {interaction['routing']}")
        print(f"  Context: {interaction['context_length']} chars")
        print(f"  Time: {interaction['timestamp']}")
        print()

    def run_interactive(self):
        """Run interactive testing session"""
        print(f"{Colors.CYAN}Interactive Mode - Type your messages (or 'quit' to exit){Colors.END}")
        print(f"{Colors.CYAN}Commands: /history, /clear, /debug, /quit{Colors.END}\n")

        username = input(f"{Colors.YELLOW}Enter your username (or press Enter for 'test_user'): {Colors.END}").strip()
        if not username:
            username = "test_user"

        print(f"\n{Colors.GREEN}✓ Ready! Start chatting with the agent...{Colors.END}\n")

        while True:
            try:
                # Get user input
                user_input = input(f"{Colors.BOLD}You ({username}): {Colors.END}").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print(f"\n{Colors.YELLOW}Exiting... Goodbye!{Colors.END}")
                    break

                elif user_input.lower() == '/history':
                    self.show_history()
                    continue

                elif user_input.lower() == '/clear':
                    self.conversation_history.clear()
                    print(f"{Colors.GREEN}✓ History cleared{Colors.END}\n")
                    continue

                elif user_input.lower() == '/debug':
                    self.debug = not self.debug
                    print(f"{Colors.GREEN}✓ Debug mode: {'ON' if self.debug else 'OFF'}{Colors.END}\n")
                    continue

                # Process the message
                interaction = self.process_message(user_input, username)
                self.display_response(interaction, username)

            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}Interrupted. Type /quit to exit or continue chatting...{Colors.END}\n")
            except Exception as e:
                print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}\n")
                if self.debug:
                    import traceback
                    traceback.print_exc()

    def show_history(self):
        """Display conversation history"""
        if not self.conversation_history:
            print(f"{Colors.YELLOW}No conversation history yet.{Colors.END}\n")
            return

        print(f"\n{Colors.HEADER}Conversation History:{Colors.END}")
        print("=" * 70)
        for i, interaction in enumerate(self.conversation_history, 1):
            print(f"{Colors.CYAN}[{i}] {interaction['timestamp']}{Colors.END}")
            print(f"  User: {interaction['user'][:60]}...")
            print(f"  Routing: {interaction['routing']} | Context: {interaction['context_length']} chars")
            print(f"  Reply: {interaction['reply'][:60]}...")
            print()
        print("=" * 70)
        print()

    def run_single_test(self, message: str, username: str = "test_user"):
        """Run a single test message"""
        interaction = self.process_message(message, username)
        self.display_response(interaction, username)
        return interaction


def main():
    parser = argparse.ArgumentParser(description="z3-Agent CLI Test Interface")
    parser.add_argument(
        '--channel',
        choices=['telegram', 'instagram'],
        default='telegram',
        help='Channel to simulate (default: telegram)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    parser.add_argument(
        '--message',
        type=str,
        help='Single message to test (non-interactive mode)'
    )
    parser.add_argument(
        '--username',
        type=str,
        default='test_user',
        help='Username for testing'
    )

    args = parser.parse_args()

    # Create tester instance
    tester = AgentTester(channel=args.channel, debug=args.debug)

    # Run mode
    if args.message:
        # Single message mode
        tester.run_single_test(args.message, args.username)
    else:
        # Interactive mode
        tester.run_interactive()


if __name__ == "__main__":
    main()
