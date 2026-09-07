import type { APIResponseModel, LoginResponse, UserPayload } from "../types/auth";
import type { AgentQueryRequest, SSEEvent } from "../types/agent";
import type { GetRequestListFilterRequest, RequestListResponse, UpdateRequestStatusRequest } from "../types/request";

const BASE_URL = import.meta.env.BACKEND_BASE_URL.replace(/\/+$/, "");

function getAuthHeader(): Record<string, string> {
	const token = localStorage.getItem("token");
	return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function loginApi(email: string, password: string): Promise<APIResponseModel<LoginResponse>> {
	const res = await fetch(`${BASE_URL}/api/auth/login`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ email, password }),
	});

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({}));
		throw new Error(errorData.detail || errorData.message || "Failed to login");
	}

	return res.json();
}

export async function getMeApi(): Promise<APIResponseModel<UserPayload>> {
	const res = await fetch(`${BASE_URL}/api/auth/me`, {
		method: "GET",
		headers: {
			...getAuthHeader(),
		},
	});

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({}));
		throw new Error(errorData.detail || errorData.message || "Failed to get user profile");
	}

	return res.json();
}

export async function getRequestsApi(filters?: GetRequestListFilterRequest): Promise<APIResponseModel<RequestListResponse>> {
	const params = new URLSearchParams();
	if (filters?.request_type) params.append("request_type", filters.request_type);
	if (filters?.status) params.append("status", filters.status);
	if (filters?.employee_number) params.append("employee_number", filters.employee_number);

	const queryString = params.toString() ? `?${params.toString()}` : "";
	const res = await fetch(`${BASE_URL}/api/request/list${queryString}`, {
		method: "GET",
		headers: {
			...getAuthHeader(),
		},
	});

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({}));
		throw new Error(errorData.detail || errorData.message || "Failed to fetch requests");
	}

	return res.json();
}

export async function acceptRequestApi(payload: UpdateRequestStatusRequest): Promise<APIResponseModel<boolean>> {
	const res = await fetch(`${BASE_URL}/api/request/accept`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			...getAuthHeader(),
		},
		body: JSON.stringify(payload),
	});

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({}));
		throw new Error(errorData.detail || errorData.message || "Failed to accept request");
	}

	return res.json();
}

export async function rejectRequestApi(payload: UpdateRequestStatusRequest): Promise<APIResponseModel<boolean>> {
	const res = await fetch(`${BASE_URL}/api/request/reject`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			...getAuthHeader(),
		},
		body: JSON.stringify(payload),
	});

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({}));
		throw new Error(errorData.detail || errorData.message || "Failed to reject request");
	}

	return res.json();
}

export async function streamChatApi(chatReq: AgentQueryRequest, onEvent: (event: SSEEvent) => void, signal?: AbortSignal): Promise<void> {
	const res = await fetch(`${BASE_URL}/api/agent/chat/stream`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			...getAuthHeader(),
		},
		body: JSON.stringify(chatReq),
		signal,
	});

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({}));
		throw new Error(errorData.detail || errorData.message || `HTTP error ${res.status}`);
	}

	if (!res.body) {
		throw new Error("No response body received for streaming");
	}

	const reader = res.body.getReader();
	const decoder = new TextDecoder("utf-8");
	let buffer = "";

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		buffer += decoder.decode(value, { stream: true });
		const lines = buffer.split("\n\n");
		// Keep the last incomplete block in buffer
		buffer = lines.pop() || "";

		for (const block of lines) {
			const trimmed = block.trim();
			if (!trimmed) continue;

			// Handle lines starting with "data: "
			const dataLines = trimmed
				.split("\n")
				.filter((line) => line.startsWith("data:"))
				.map((line) => line.replace(/^data:\s*/, ""));

			for (const jsonStr of dataLines) {
				try {
					const parsed = JSON.parse(jsonStr) as SSEEvent;
					onEvent(parsed);
				} catch (e) {
					console.warn("Failed to parse SSE JSON chunk:", jsonStr, e);
				}
			}
		}
	}

	// Flush remaining buffer if any
	if (buffer.trim()) {
		const dataLines = buffer
			.trim()
			.split("\n")
			.filter((line) => line.startsWith("data:"))
			.map((line) => line.replace(/^data:\s*/, ""));

		for (const jsonStr of dataLines) {
			try {
				const parsed = JSON.parse(jsonStr) as SSEEvent;
				onEvent(parsed);
			} catch (e) {
				console.warn("Failed to parse final SSE JSON chunk:", jsonStr, e);
			}
		}
	}
}
