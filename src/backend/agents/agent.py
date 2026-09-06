import logging
from typing import List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from ..configs.openai_config import OpenAIConfig
from ..models.agent_model import AgentQueryRequest, AgentQueryResponse, ChatMessage
from ..prompts.agent_prompts import AGENT_SYSTEM_PROMPT, ROUTER_SYSTEM_PROMPT
from ..tools.employee_tools import (
    get_employee_profile,
    get_health_benefit,
    get_leave_balance,
    submit_benefit_claim,
    submit_expense_claim,
    submit_leave_request
)
from ..tools.policy_retrieval_tool import search_hr_policies


class Agent:
    def __init__(self):
        self._tools = [
            search_hr_policies,
            get_employee_profile,
            get_leave_balance,
            get_health_benefit,
            submit_leave_request,
            submit_benefit_claim,
            submit_expense_claim
        ]
        self._tool_map = {t.name: t for t in self._tools}

    def ask(self, request: AgentQueryRequest) -> AgentQueryResponse:
        logging.info(f"[INFO][agent.py][ask] Processing query: '{request.query}'")
        try:
            model_name = self._route_model(request.query, request.chat_history)
            logging.info(f"[INFO][agent.py][ask] LLM Model Router selected tier: {model_name}")

            llm = ChatOpenAI(
                model = model_name,
                api_key = OpenAIConfig.API_KEY,
                temperature = 0.0
            )
            llm_with_tools = llm.bind_tools(self._tools)

            history_messages = []
            if request.chat_history:
                for msg in request.chat_history:
                    if msg.role == "user":
                        history_messages.append(HumanMessage(content = msg.content))
                    elif msg.role == "assistant":
                        history_messages.append(AIMessage(content = msg.content))
                    elif msg.role == "system":
                        history_messages.append(SystemMessage(content = msg.content))

            prompt_text = request.query
            if request.policy_id:
                prompt_text = f"{request.query} (Policy ID: {request.policy_id})"

            messages = [SystemMessage(content = AGENT_SYSTEM_PROMPT)]
            messages.extend(history_messages)
            messages.append(HumanMessage(content = prompt_text))

            response = llm_with_tools.invoke(messages)

            updated_history: List[ChatMessage] = list(request.chat_history) if request.chat_history else []
            updated_history.append(ChatMessage(role = "user", content = prompt_text))

            if response.tool_calls:
                messages.append(response)
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    call_id = tool_call["id"]

                    if tool_name in self._tool_map:
                        tool_func = self._tool_map[tool_name]
                        tool_output = tool_func.invoke(tool_args)
                        tool_output_str = str(tool_output)

                        messages.append(
                            ToolMessage(
                                content = tool_output_str,
                                tool_call_id = call_id,
                                name = tool_name
                            )
                        )

                final_response = llm_with_tools.invoke(messages)
                answer_text = str(final_response.content)
            else:
                answer_text = str(response.content)

            updated_history.append(ChatMessage(role = "assistant", content = answer_text))

            agent_response = AgentQueryResponse(
                query = request.query,
                answer = answer_text,
                model_used = model_name,
                chat_history = updated_history
            )
            return agent_response
        except Exception as e:
            logging.error(f"[ERROR][agent.py][ask] Failed to process agent query. Error: {e}")
            raise e

    def _route_model(self, query: str, chat_history: Optional[List[ChatMessage]] = None) -> str:
        logging.info("[INFO][agent.py][_route_model] Routing query with LLM (OPENAI_SMALL_MODEL) including recent chat history.")
        try:
            router_llm = ChatOpenAI(
                model = OpenAIConfig.OPENAI_SMALL_MODEL,
                api_key = OpenAIConfig.API_KEY,
                temperature = 0.0
            )

            history_context = ""
            if chat_history:
                recent_history = chat_history[-6:]
                history_lines = [f"{msg.role.upper()}: {msg.content[:150]}" for msg in recent_history]
                history_context = "\n".join(history_lines)

            prompt_content = query
            if history_context:
                prompt_content = f"Recent Conversation Context:\n{history_context}\n\nCurrent User Query: {query}"

            messages = [
                SystemMessage(content = ROUTER_SYSTEM_PROMPT),
                HumanMessage(content = prompt_content)
            ]
            response = router_llm.invoke(messages)
            tier = str(response.content).strip().upper()

            if "LARGE" in tier:
                return OpenAIConfig.OPENAI_LARGE_MODEL
            elif "MEDIUM" in tier:
                return OpenAIConfig.OPENAI_MEDIUM_MODEL
            else:
                return OpenAIConfig.OPENAI_SMALL_MODEL
        except Exception as e:
            logging.warning(f"[WARNING][agent.py][_route_model] LLM routing failed, falling back to baseline SMALL model. Error: {e}")
            return OpenAIConfig.OPENAI_SMALL_MODEL
