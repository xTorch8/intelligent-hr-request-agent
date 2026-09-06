import logging
from typing import List

from ..agents.agent import Agent
from ..models.agent_model import AgentQueryRequest, ChatMessage


def run_multi_turn_test():
    logging.basicConfig(level = logging.INFO)
    agent = Agent()

    turns = [
        "What is the maximum duration for an annual leave request?",
        "How many days in advance should I request it?",
        "What if I need an exception to this limit?"
    ]

    chat_history: List[ChatMessage] = []

    print("==================================================")
    print("      Multi-Turn Agent Chat History Test         ")
    print("==================================================\n")

    for turn_num, user_query in enumerate(turns, start = 1):
        print(f"💬 Turn {turn_num} User Query: '{user_query}'")
        print("-" * 60)

        request = AgentQueryRequest(
            query = user_query,
            chat_history = chat_history
        )

        try:
            response = agent.ask(request)
            print(f"🤖 Model Tier: [{response.model_used}]")
            print(f"🗣️ Agent Response:\n{response.answer}\n")
            print(f"📜 Updated Transcript Messages Count: {len(response.chat_history)}")

            # Pass updated conversation history to next turn
            chat_history = response.chat_history
        except Exception as e:
            print(f"❌ Error during Turn {turn_num}: {e}")

        print("=" * 60 + "\n")


if __name__ == "__main__":
    run_multi_turn_test()

