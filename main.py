"""
WQ LLM — Wellness Quotient AI Coach
Main entry point for the interactive chat interface.

Usage:
    export GEMINI_API_KEY=your_key_here
    python main.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.wellness_agent import WellnessAgent
from core.ontology_agent import get_ontology_agent
from core.utils import log_step, log_info


WELCOME_MESSAGE = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🌿  WELLNESS QUOTIENT AI COACH  🌿                ║
║                                                              ║
║   Your personal wellness guide — warm, knowledgeable,        ║
║   and always in your corner.                                 ║
║                                                              ║
║   Type your message to start.                                ║
║   Type 'quit' to exit.                                       ║
║   Type 'status' to see your profile.                         ║
║   Type 'ontology' to explore the knowledge base.             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


async def explore_ontology():
    """Interactive ontology explorer — shows the component-based knowledge graph."""
    agent = get_ontology_agent()
    summary = agent.get_summary()

    print(f"\n📚 {summary['name']} v{summary['version']}")
    print("=" * 60)
    print("\n  Components (like Telco Ontology sidebar):")
    print("  " + "-" * 56)

    total_entities = 0
    total_instances = 0
    total_ops = 0

    for c in summary["components"]:
        print(f"  {c['icon']}  {c['name']}")
        print(f"      {c['entities']} entities | {c['instances']} instances | {c['operations']} operations")
        total_entities += c["entities"]
        total_instances += c["instances"]
        total_ops += c["operations"]

    print("  " + "-" * 56)
    print(f"  TOTAL: {len(summary['components'])} components, {total_entities} entities, {total_instances} instances, {total_ops} operations")

    # Show cross-component relationships
    print("\n  Cross-Component Relationships:")
    rel_graph = agent.registry.get("relationship_graph", {})
    for cid, rels in rel_graph.items():
        for rel_type, targets in rels.items():
            if isinstance(targets, list):
                print(f"    {cid} --{rel_type}--> {', '.join(targets)}")

    print()


async def show_status(agent: WellnessAgent):
    """Show current conversation/user state."""
    state = agent.state.to_dict()
    print("\n📋 Current Status")
    print("=" * 50)
    print(f"  Phase: {state['phase']}")
    print(f"  Messages: {state['message_count']}")

    if state["user_profile"]:
        print("  Profile:")
        for k, v in state["user_profile"].items():
            print(f"    - {k}: {v}")

    if state["identified_conditions"]:
        print(f"  Conditions: {', '.join(state['identified_conditions'])}")

    if state["active_interventions"]:
        print(f"  Active Interventions: {', '.join(state['active_interventions'])}")

    print()


async def main():
    """Main interactive loop."""
    print(WELCOME_MESSAGE)

    # Load ontology agent (component-based, like Totogi Ontology Agent)
    log_step("Loading WQ Ontology Agent...", symbol="🧬")
    ontology = get_ontology_agent()

    # Initialize wellness coaching agent
    log_step("Initializing Wellness Agent...", symbol="🤖")
    try:
        agent = WellnessAgent(use_reasoning=True)
    except Exception as e:
        log_step(f"Failed to initialize with reasoning. Trying without: {e}", symbol="⚠️")
        agent = WellnessAgent(use_reasoning=False)

    print("\n🌿 Hi! I'm your Wellness Quotient AI Coach.")
    print("   Tell me — what's on your mind about your health today?\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n🌿 Take care! Remember — small steps, every day. 💚")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("\n🌿 Take care! Remember — small steps, every day. 💚")
            break

        if user_input.lower() == "status":
            await show_status(agent)
            continue

        if user_input.lower() == "ontology":
            await explore_ontology()
            continue

        # Process the message
        try:
            response = await agent.chat(user_input)
            print(f"\n🌿 Coach: {response}\n")
        except Exception as e:
            log_step(f"Error: {e}", symbol="❌")
            print(f"\n⚠️ Something went wrong: {e}")
            print("   Please try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    asyncio.run(main())
