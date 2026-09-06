import logging

from ..agents.agent import Agent
from ..models.agent_model import AgentQueryRequest


def run_agent_test():
    logging.basicConfig(level = logging.INFO)
    agent = Agent()

    sample_questions = [
        "What is the maximum duration for an annual leave request?",
        "How many days in advance should I submit ordinary annual leave requests?",
        "Can Human Resources approve an exception to the notice or maximum duration requirement?",
        "What is the medical documentation requirement for sick leave?"
    ]

    print("==================================================")
    print("        LangChain Agent Evaluation Test          ")
    print("==================================================\n")

    for question in sample_questions:
        print(f"👤 Question: '{question}'")
        print("-" * 60)
        request = AgentQueryRequest(query = question)
        try:
            response = agent.ask(request)
            print(f"🤖 Model Selected (via LLM Router): [{response.model_used}]")
            print(f"💬 Agent Answer:\n{response.answer}\n")
        except Exception as e:
            print(f"❌ Error during agent execution: {e}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    run_agent_test()
