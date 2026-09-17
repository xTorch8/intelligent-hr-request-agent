import React, { useEffect, useRef, useState } from "react";
import type { ChatMessage, ToolStep } from "../types/agent";
import { streamChatApi, uploadFileApi } from "../services/api";
import { useAuth } from "../context/AuthContext";

export const ChatbotPage: React.FC = () => {
	const { user } = useAuth();
	const [messages, setMessages] = useState<ChatMessage[]>([]);

	useEffect(() => {
		const firstName = user?.first_name || "Employee";
		const greeting = `Hello ${firstName}! 👋 I am your Intelligent HR Assistant. I can help answer HR policy questions, check your leave balances, calculate reimbursement amounts, or submit leave & claim requests. How can I assist you today?`;

		setMessages((prev) => {
			if (prev.length === 0) {
				return [{ role: "assistant", content: greeting }];
			}
			if (prev.length === 1 && prev[0].role === "assistant" && prev[0].content.startsWith("Hello ")) {
				return [{ role: "assistant", content: greeting }];
			}
			return prev;
		});
	}, [user?.first_name]);

	const [inputQuery, setInputQuery] = useState("");
	const [inputValidationError, setInputValidationError] = useState<string | null>(null);

	// File upload state
	const [uploadingFile, setUploadingFile] = useState<boolean>(false);
	const [attachedBlob, setAttachedBlob] = useState<{ url: string; filename: string } | null>(null);
	const fileInputRef = useRef<HTMLInputElement>(null);

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
		if (!trimmed && !attachedBlob) {
			return "Please enter a message or policy inquiry before sending.";
		}
		if (trimmed.length > 1000) {
			return `Your query is too long (${trimmed.length}/1000 characters). Please shorten your message.`;
		}
		return null;
	};

	const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
		const files = e.target.files;
		if (!files || files.length === 0) return;

		const file = files[0];
		setUploadingFile(true);
		setStreamError(null);

		try {
			const res = await uploadFileApi(file);
			if (res.is_success && res.payload) {
				setAttachedBlob({
					url: res.payload.blob_url,
					filename: res.payload.original_filename || res.payload.filename || file.name,
				});
			} else {
				setStreamError(res.message || res.error || "Please contact developer");
			}
		} catch (err: unknown) {
			setStreamError((err as Error).message || "Please contact developer");
		} finally {
			setUploadingFile(false);
			if (fileInputRef.current) {
				fileInputRef.current.value = "";
			}
		}
	};

	const renderMessageContent = (content: string, role: string) => {
		if (role !== "user") {
			return content;
		}

		const urlMatch = content.match(/Attached Document URL:\s*(https?:\/\/\S+)/i);
		if (urlMatch) {
			const cleanText = content.replace(/Attached Document URL:\s*https?:\/\/\S+/gi, "").trim();
			const fullUrl = urlMatch[1];
			const urlParts = fullUrl.split("/");
			const filenameWithUuid = urlParts[urlParts.length - 1].split("?")[0];
			const displayFilename = filenameWithUuid.includes("_") ? filenameWithUuid.split("_").slice(1).join("_") : filenameWithUuid;

			return (
				<div className="space-y-2">
					<div>{cleanText || "Document attached for HR request."}</div>
					<div className="inline-flex items-center space-x-1.5 bg-indigo-700/60 border border-indigo-400/40 text-indigo-100 px-2.5 py-1 rounded-lg text-xs font-semibold">
						<span>📎 Attachment: {decodeURIComponent(displayFilename) || "Document"}</span>
					</div>
				</div>
			);
		}

		return content;
	};

	const handleSend = async (queryToSend?: string) => {
		const rawQuery = (queryToSend || inputQuery).trim();

		const validationErr = validateQuery(rawQuery);
		if (validationErr) {
			setInputValidationError(validationErr);
			return;
		}

		const attachmentUrl = attachedBlob?.url;
		const queryForAgent = attachmentUrl ? `${rawQuery}\nAttached Document URL: ${attachmentUrl}` : rawQuery;

		setInputQuery("");
		setAttachedBlob(null);
		setInputValidationError(null);
		setStreamError(null);
		setIsStreaming(true);
		setCurrentStreamText("");
		setActiveTools([]);
		setModelUsed(null);

		const userMessage: ChatMessage = { role: "user", content: queryForAgent };
		const updatedHistory = [...messages, userMessage];
		setMessages(updatedHistory);

		const controller = new AbortController();
		abortControllerRef.current = controller;

		let accumulatedText = "";

		try {
			await streamChatApi(
				{
					query: queryForAgent,
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
						const finalAnswer = eventData.response.answer || accumulatedText || "I have processed your request.";
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
		<div className="flex flex-col h-[calc(100vh-65px)] bg-slate-50 text-slate-900 font-sans">
			{/* Header Bar */}
			<div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white shadow-xs">
				<div className="flex items-center space-x-3">
					<div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center font-bold text-white shadow-sm">
						AI
					</div>
					<div>
						<h1 className="font-semibold text-slate-900 text-sm sm:text-base">HR Policy & Request Agent</h1>
						<p className="text-xs text-slate-500">Policy-Grounded RAG • Interactive Session</p>
					</div>
				</div>
				{modelUsed && (
					<span className="hidden sm:inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 border border-indigo-200 text-indigo-700">
						Model: {modelUsed}
					</span>
				)}
			</div>

			{/* Stream Error Alert Banner */}
			{streamError && (
				<div className="bg-red-50 border-b border-red-200 px-6 py-2.5 text-xs text-red-800 flex items-center justify-between">
					<span className="flex items-center space-x-2">
						<span>⚠️</span>
						<span>{streamError}</span>
					</span>
					<button onClick={() => setStreamError(null)} className="text-red-600 hover:text-red-900 font-bold px-2 py-0.5">
						Dismiss
					</button>
				</div>
			)}

			{/* Messages Container */}
			<div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
				{messages.map((msg, idx) => (
					<div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
						<div
							className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 shadow-sm leading-relaxed text-sm ${
								msg.role === "user" ? "bg-indigo-600 text-white rounded-br-none" : "bg-white text-slate-800 border border-slate-200 rounded-bl-none"
							}`}
						>
							<div className="whitespace-pre-wrap">{renderMessageContent(msg.content, msg.role)}</div>
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
										className="flex items-center space-x-2 text-xs bg-white border border-indigo-200 text-indigo-800 px-3 py-2 rounded-xl shadow-xs"
									>
										{t.status === "running" ? (
											<svg className="animate-spin h-3.5 w-3.5 text-indigo-600" fill="none" viewBox="0 0 24 24">
												<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
												<path
													className="opacity-75"
													fill="currentColor"
													d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
												></path>
											</svg>
										) : (
											<span className="text-emerald-600 font-bold">✓</span>
										)}
										<span>{getToolDisplayName(t.tool)}</span>
									</div>
								))}
							</div>
						)}

						{/* Token Streaming Message Box */}
						<div className="max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm text-sm">
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
					<p className="text-xs text-slate-500 font-medium mb-2">Suggested Inquiries:</p>
					<div className="flex flex-wrap gap-2">
						{quickPrompts.map((prompt, i) => (
							<button
								key={i}
								onClick={() => handleSend(prompt)}
								className="text-xs bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 text-slate-700 hover:text-indigo-700 px-3 py-1.5 rounded-lg transition text-left shadow-xs"
							>
								{prompt}
							</button>
						))}
					</div>
				</div>
			)}

			{/* Hidden File Input */}
			<input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />

			{/* Input Area */}
			<div className="p-4 border-t border-slate-200 bg-white">
				<form
					onSubmit={(e) => {
						e.preventDefault();
						handleSend();
					}}
					className="max-w-5xl mx-auto space-y-2"
				>
					{inputValidationError && (
						<div className="text-xs text-red-600 flex items-center space-x-1 px-1">
							<span>⚠️</span>
							<span>{inputValidationError}</span>
						</div>
					)}

					{/* Attached File Chip */}
					{attachedBlob && (
						<div className="flex items-center space-x-2 bg-indigo-50 border border-indigo-200 text-indigo-800 px-3 py-1.5 rounded-xl text-xs w-fit">
							<span>📎 {attachedBlob.filename}</span>
							<button type="button" onClick={() => setAttachedBlob(null)} className="text-indigo-600 hover:text-indigo-900 font-bold ml-1">
								✕
							</button>
						</div>
					)}

					<div className="flex items-center space-x-2 sm:space-x-3">
						<button
							type="button"
							onClick={() => fileInputRef.current?.click()}
							disabled={isStreaming || uploadingFile}
							title="Attach Receipt or Document"
							className="p-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition border border-slate-200 disabled:opacity-50 flex items-center justify-center"
						>
							{uploadingFile ? (
								<svg className="animate-spin h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24">
									<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
									<path
										className="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
									></path>
								</svg>
							) : (
								<svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path
										strokeLinecap="round"
										strokeLinejoin="round"
										strokeWidth="2"
										d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
									/>
								</svg>
							)}
						</button>

						<input
							type="text"
							value={inputQuery}
							onChange={(e) => {
								setInputQuery(e.target.value);
								if (inputValidationError) setInputValidationError(null);
							}}
							disabled={isStreaming}
							placeholder="Ask about policies, balances, or submit an HR request..."
							className={`flex-1 bg-slate-50 border rounded-xl px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none transition disabled:opacity-50 ${
								inputValidationError ? "border-red-500 focus:ring-2 focus:ring-red-500/20" : "border-slate-200 focus:ring-2 focus:ring-indigo-500"
							}`}
						/>

						{isStreaming ? (
							<button
								type="button"
								onClick={handleStop}
								className="px-4 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl text-sm font-semibold transition flex items-center space-x-1 shadow-md shadow-red-600/20"
							>
								<svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
									<rect x="6" y="6" width="12" height="12" rx="2" />
								</svg>
								<span>Stop</span>
							</button>
						) : (
							<button
								type="submit"
								disabled={!inputQuery.trim() && !attachedBlob}
								className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-600/20 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center space-x-2"
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
