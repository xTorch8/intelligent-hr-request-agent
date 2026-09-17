export type RequestTypeFilter = "LEAVE" | "EXPENSE" | "BENEFIT";

export type RequestStatusFilter = "SUBMITTED" | "PROCESSING" | "PENDING_REVIEW" | "APPROVED" | "REJECTED" | "COMPLETED" | "CANCELLED";

export interface RequestSummaryItem {
	request_id: string;
	request_number: string;
	employee_id: string;
	employee_number: string;
	employee_name: string;
	department: string;
	request_type: string;
	status: string;
	title: string;
	description?: string | null;
	blob_url?: string | null;
	recommendation?: string | null;
	eligibility_result?: string | null;
	reasoning_summary?: string | null;
	decision_reason?: string | null;
	submitted_at: string;
	updated_at: string;
}

export interface RequestListResponse {
	total_count: number;
	page: number;
	page_size: number;
	total_pages: number;
	requests: RequestSummaryItem[];
}

export interface GetRequestListFilterRequest {
	request_type?: RequestTypeFilter | string;
	status?: RequestStatusFilter | string;
	employee_number?: string;
	my_requests_only?: boolean;
	page?: number;
	page_size?: number;
}

export interface UpdateRequestStatusRequest {
	request_id: string;
	actor_id?: string;
	reason?: string;
}

export interface CancelRequestInput {
	request_id: string;
	reason?: string;
}

export interface RuleCheckResult {
	rule_name: string;
	passed: boolean;
	details: string;
}
