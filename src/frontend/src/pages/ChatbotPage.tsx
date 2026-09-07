import React, { useEffect, useRef, useState } from "react";
import type { ChatMessage, ToolStep } from "../types/agent";
import { streamChatApi } from "../services/api";
import { useAuth } from "../context/AuthContext";

export const ChatbotPage: React.FC = () => {
	const { user } = useAuth();
	const [messages, setMessages] = useState<ChatMessage[]>([
		{
			role: "assistant",
			content: `Hello ${user?.first_name || "Employee"}! 👋 I am your Intelligent HR Assistant. I can help answer HR policy questions, check your leave balances, calculate reimbursement amounts, or submit leave & claim requests. How can I assist you today?`,
		},
	]);
	const [inputQuery, setInputQuery] = useState("");
	const [inputValidationError, setInputValidationError] = useState<string | null>(null);

	const [isStreaming, setIsStreaming] = useState(false);
	const [currentStreamText, setCurrentStreamText] = useState("");
	const [activeTools, setActiveTools] = useState<ToolStep[]>([]);
	const [modelUsed, setModelUsed] = useState<string | null>(null);
	const [streamError, setStreamError] = useState<string | null>(null);

	const messagesEndRef = useRef<HTMLDivElement>(null);
	const abortControllerRef = useRef<AbortController | null>(null);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages, currentStreamText, activeTools]);

	const quickPrompts = [
		"What is the policy for annual leave and notice period?",
		"Check my current leave balance and employee profile.",
		"I want to request 2 days annual leave from 2026-10-01 to 2026-10-02.",
		"What are the expense claim limits for travel and internet?",
	];

	const validateQuery = (query: string): string | null => {
		const trimmed = query.trim();
		if (!trimmed) {
			return "Please enter a message or policy inquiry before sending.";
		}
		if (trimmed.length > 1000) {
			return `Your query is too long (${trimmed.length}/1000 characters). Please shorten your message.`;
		}
		return null;
	};

	const handleSend = async (queryToSend?: string) => {
		const query = (queryToSend || inputQuery).trim();

		// Validation check
		const validationErr = validateQuery(query);
		if (validationErr) {
			setInputValidationError(validationErr);
			return;
		}

		setInputQuery("");
		setInputValidationError(null);
		setStreamError(null);
		setIsStreaming(true);
		setCurrentStreamText("");
		setActiveTools([]);
		setModelUsed(null);

		const userMessage: ChatMessage = { role: "user", content: query };
		const updatedHistory = [...messages, userMessage];
		setMessages(updatedHistory);

		const controller = new AbortController();
		abortControllerRef.current = controller;

		let accumulatedText = "";

		try {
			await streamChatApi(
				{
					query,
					chat_history: updatedHistory.slice(-10),
				},
				(eventData) => {
					if (eventData.event === "metadata") {
						setModelUsed(eventData.model_used);
					} else if (eventData.event === "tool_start") {
						setActiveTools((prev) => [...prev, { tool: eventData.tool, args: eventData.args, status: "running" }]);
					} else if (eventData.event === "tool_end") {
						setActiveTools((prev) => prev.map((t) => (t.tool === eventData.tool ? { ...t, result: eventData.result, status: "completed" } : t)));
					} else if (eventData.event === "token") {
						accumulatedText += eventData.token;
						setCurrentStreamText(accumulatedText);
					} else if (eventData.event === "done") {
						const finalAnswer = eventData.response.answer || accumulatedText;
						setMessages((prev) => [...prev, { role: "assistant", content: finalAnswer }]);
						setCurrentStreamText("");
						setActiveTools([]);
						setIsStreaming(false);
					} else if (eventData.event === "error") {
						setStreamError(`Agent Error: ${eventData.error}`);
						setMessages((prev) => [...prev, { role: "assistant", content: `❌ Error: ${eventData.error}` }]);
						setCurrentStreamText("");
						setIsStreaming(false);
					}
				},
				controller.signal,
			);
		} catch (err: unknown) {
			if ((err as Error).name === "AbortError") {
				if (accumulatedText) {
					setMessages((prev) => [...prev, { role: "assistant", content: accumulatedText + " _(stopped by user)_" }]);
				}
			} else {
				const errorMsg = (err as Error).message || "Stream connection failed";
				setStreamError(errorMsg);
				setMessages((prev) => [...prev, { role: "assistant", content: `⚠️ Failed to get agent response: ${errorMsg}` }]);
			}
		} finally {
			setCurrentStreamText("");
			setIsStreaming(false);
			abortControllerRef.current = null;
		}
	};

	const handleStop = () => {
		if (abortControllerRef.current) {
			abortControllerRef.current.abort();
		}
	};

	const getToolDisplayName = (tool: string) => {
		switch (tool) {
			case "search_hr_policies":
				return "🔍 Searching Policy Knowledgebase";
			case "get_employee_profile":
				return "👤 Retrieving Employee Profile";
			case "get_leave_balance":
				return "📅 Checking Leave Balances";
			case "get_health_benefit":
				return "🏥 Checking Health Benefit Plan";
			case "submit_leave_request":
				return "📝 Processing Leave Request Submission";
			case "submit_expense_claim":
				return "💳 Processing Expense Claim Submission";
			case "submit_benefit_claim":
				return "🩺 Processing Benefit Claim Submission";
			default:
				return `⚙️ Running ${tool}`;
		}
	};

	return (
		<div className="flex flex-col h-[calc(100vh-65px)] bg-slate-950 text-slate-100 font-sans">
			{/* Header Bar */}
			<div className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-900/60 backdrop-blur">
				<div className="flex items-center space-x-3">
					<div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-md">
						AI
					</div>
					<div>
						<h1 className="font-semibold text-white text-sm sm:text-base">HR Policy & Request Agent</h1>
						<p className="text-xs text-slate-400">Policy-Grounded RAG • Interactive Session</p>
					</div>
				</div>
				{modelUsed && (
					<span className="hidden sm:inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
						Model: {modelUsed}
					</span>
				)}
			</div>

			{/* Stream Error Alert Banner */}
			{streamError && (
				<div className="bg-red-500/10 border-b border-red-500/30 px-6 py-2 text-xs text-red-300 flex items-center justify-between">
					<span className="flex items-center space-x-2">
						<span>⚠️</span>
						<span>{streamError}</span>
					</span>
					<button onClick={() => setStreamError(null)} className="text-red-400 hover:text-white font-bold px-2 py-0.5">
						Dismiss
					</button>
				</div>
			)}

			{/* Messages Container */}
			<div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
				{messages.map((msg, idx) => (
					<div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
						<div
							className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 shadow-md leading-relaxed text-sm ${
								msg.role === "user"
									? "bg-indigo-600 text-white rounded-br-none"
									: "bg-slate-800/90 text-slate-200 border border-slate-700/70 rounded-bl-none"
							}`}
						>
							<div className="whitespace-pre-wrap">{msg.content}</div>
						</div>
					</div>
				))}

				{/* Live Streaming State */}
				{isStreaming && (
					<div className="flex flex-col items-start space-y-3">
						{/* Tool Executions */}
						{activeTools.length > 0 && (
							<div className="space-y-1.5 w-full max-w-[75%]">
								{activeTools.map((t, index) => (
									<div
										key={index}
										className="flex items-center space-x-2 text-xs bg-slate-900/80 border border-indigo-500/30 text-indigo-300 px-3 py-2 rounded-xl"
									>
										{t.status === "running" ? (
											<svg className="animate-spin h-3.5 w-3.5 text-indigo-400" fill="none" viewBox="0 0 24 24">
												<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
												<path
													className="opacity-75"
													fill="currentColor"
													d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
												></path>
											</svg>
										) : (
											<span className="text-emerald-400 font-bold">✓</span>
										)}
										<span>{getToolDisplayName(t.tool)}</span>
									</div>
								))}
							</div>
						)}

						{/* Token Streaming Message Box */}
						<div className="max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 bg-slate-800/90 text-slate-200 border border-slate-700/70 rounded-bl-none shadow-md text-sm">
							<div className="whitespace-pre-wrap">
								{currentStreamText || (
									<span className="inline-flex items-center space-x-1 text-slate-400 italic">
										<span>Thinking</span>
										<span className="animate-pulse">...</span>
									</span>
								)}
							</div>
						</div>
					</div>
				)}

				<div ref={messagesEndRef} />
			</div>

			{/* Suggested Prompts */}
			{!isStreaming && messages.length <= 2 && (
				<div className="px-6 py-2">
					<p className="text-xs text-slate-400 font-medium mb-2">Suggested Inquiries:</p>
					<div className="flex flex-wrap gap-2">
						{quickPrompts.map((prompt, i) => (
							<button
								key={i}
								onClick={() => handleSend(prompt)}
								className="text-xs bg-slate-900 hover:bg-indigo-600/20 border border-slate-800 hover:border-indigo-500/50 text-slate-300 hover:text-indigo-300 px-3 py-1.5 rounded-lg transition text-left"
							>
								{prompt}
							</button>
						))}
					</div>
				</div>
			)}

			{/* Input Area */}
			<div className="p-4 border-t border-slate-800 bg-slate-900/80">
				<form
					onSubmit={(e) => {
						e.preventDefault();
						handleSend();
					}}
					className="max-w-5xl mx-auto space-y-2"
				>
					{inputValidationError && (
						<div className="text-xs text-red-400 flex items-center space-x-1 px-1">
							<span>⚠️</span>
							<span>{inputValidationError}</span>
						</div>
					)}

					<div className="flex items-center space-x-3">
						<input
							type="text"
							value={inputQuery}
							onChange={(e) => {
								setInputQuery(e.target.value);
								if (inputValidationError) setInputValidationError(null);
							}}
							disabled={isStreaming}
							placeholder="Ask about policies, balances, or submit an HR request..."
							className={`flex-1 bg-slate-950 border rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none transition disabled:opacity-50 ${
								inputValidationError ? "border-red-500 focus:ring-2 focus:ring-red-500/50" : "border-slate-800 focus:ring-2 focus:ring-indigo-500"
							}`}
						/>

						{isStreaming ? (
							<button
								type="button"
								onClick={handleStop}
								className="px-4 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl text-sm font-semibold transition flex items-center space-x-1 shadow-lg shadow-red-600/20"
							>
								<svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
									<rect x="6" y="6" width="12" height="12" rx="2" />
								</svg>
								<span>Stop</span>
							</button>
						) : (
							<button
								type="submit"
								disabled={!inputQuery.trim()}
								className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center space-x-2"
							>
								<span>Send</span>
								<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
								</svg>
							</button>
						)}
					</div>
				</form>
			</div>
		</div>
	);
};
