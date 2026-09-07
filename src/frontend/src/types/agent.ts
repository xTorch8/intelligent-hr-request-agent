export interface ChatMessage {
	role: "user" | "assistant" | "system";
	content: string;
	tool_name?: string;
	tool_call_id?: string;
}

export interface AgentQueryRequest {
	query: string;
	policy_id?: string;
	chat_history?: ChatMessage[];
}

export interface AgentQueryResponse {
	query: string;
	answer: string;
	model_used: string;
	chat_history: ChatMessage[];
}

export interface ToolStep {
	tool: string;
	args?: Record<string, unknown>;
	result?: string;
	status: "running" | "completed";
}

export type SSEEvent =
	| { event: "metadata"; model_used: string }
	| { event: "tool_start"; tool: string; args?: Record<string, unknown> }
	| { event: "tool_end"; tool: string; result?: string }
	| { event: "token"; token: string }
	| { event: "done"; response: AgentQueryResponse }
	| { event: "error"; error: string };
