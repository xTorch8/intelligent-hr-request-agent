import React, { useCallback, useEffect, useState } from "react";
import type { RequestSummaryItem } from "../types/request";
import { acceptRequestApi, getRequestsApi, rejectRequestApi } from "../services/api";

export const DashboardPage: React.FC = () => {
	const [requests, setRequests] = useState<RequestSummaryItem[]>([]);
	const [loading, setLoading] = useState<boolean>(true);
	const [error, setError] = useState<string | null>(null);

	// Filters
	const [selectedType, setSelectedType] = useState<string>("");
	const [selectedStatus, setSelectedStatus] = useState<string>("");
	const [searchEmployee, setSearchEmployee] = useState<string>("");

	// Pagination
	const [page, setPage] = useState<number>(1);
	const [pageSize] = useState<number>(10);
	const [totalPages, setTotalPages] = useState<number>(1);
	const [totalCount, setTotalCount] = useState<number>(0);

	// Modal Detail & Decision State
	const [selectedRequest, setSelectedRequest] = useState<RequestSummaryItem | null>(null);
	const [actionReason, setActionReason] = useState<string>("");
	const [actionReasonError, setActionReasonError] = useState<string | null>(null);
	const [actionLoading, setActionLoading] = useState<boolean>(false);
	const [actionFeedback, setActionFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);
	const [confirmAction, setConfirmAction] = useState<"accept" | "reject" | null>(null);

	const fetchRequests = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const res = await getRequestsApi({
				request_type: selectedType || undefined,
				status: selectedStatus || undefined,
				employee_number: searchEmployee.trim() || undefined,
				page,
				page_size: pageSize,
			});

			if (res.is_success && res.payload) {
				setRequests(res.payload.requests || []);
				setTotalPages(res.payload.total_pages || 1);
				setTotalCount(res.payload.total_count || 0);
			} else {
				setError(res.message || "Failed to load HR request list.");
			}
		} catch (err: unknown) {
			setError((err as Error).message || "An error occurred while fetching HR requests.");
		} finally {
			setLoading(false);
		}
	}, [selectedType, selectedStatus, searchEmployee, page, pageSize]);

	useEffect(() => {
		fetchRequests();
	}, [fetchRequests]);

	const handleInitiateAction = (action: "accept" | "reject") => {
		setActionReasonError(null);
		setActionFeedback(null);

		if (!selectedRequest) return;

		if (selectedRequest.status === "APPROVED" || selectedRequest.status === "REJECTED" || selectedRequest.status === "CANCELLED") {
			setActionFeedback({
				type: "error",
				message: `This request is already ${selectedRequest.status} and cannot be modified further.`,
			});
			return;
		}

		if (action === "reject" && !actionReason.trim()) {
			setActionReasonError("A rejection reason is required so the employee understands why their request was declined.");
			return;
		}

		setConfirmAction(action);
	};

	const handleExecuteStatusUpdate = async () => {
		if (!selectedRequest || !confirmAction) return;

		const action = confirmAction;
		setConfirmAction(null);
		setActionLoading(true);
		setActionFeedback(null);
		setActionReasonError(null);

		try {
			const apiCall = action === "accept" ? acceptRequestApi : rejectRequestApi;
			const res = await apiCall({
				request_id: selectedRequest.request_id,
				reason: actionReason.trim() || undefined,
			});

			if (res.is_success) {
				const newStatus = action === "accept" ? "APPROVED" : "REJECTED";
				setActionFeedback({
					type: "success",
					message: `Request ${selectedRequest.request_number} has been successfully ${newStatus.toLowerCase()}.`,
				});
				setActionReason("");
				fetchRequests();
				setSelectedRequest((prev) => (prev ? { ...prev, status: newStatus } : null));
			} else {
				setActionFeedback({
					type: "error",
					message: res.message || res.error || `Failed to ${action} request. Please try again.`,
				});
			}
		} catch (err: unknown) {
			setActionFeedback({
				type: "error",
				message: (err as Error).message || `Network error encountered while attempting to ${action} request.`,
			});
		} finally {
			setActionLoading(false);
		}
	};

	const getStatusBadge = (status: string) => {
		switch (status.toUpperCase()) {
			case "APPROVED":
				return "bg-emerald-50 text-emerald-700 border-emerald-200";
			case "REJECTED":
				return "bg-red-50 text-red-700 border-red-200";
			case "CANCELLED":
				return "bg-slate-100 text-slate-600 border-slate-300";
			case "PENDING_REVIEW":
			case "SUBMITTED":
				return "bg-amber-50 text-amber-700 border-amber-200";
			default:
				return "bg-slate-50 text-slate-600 border-slate-200";
		}
	};

	const getTypeBadge = (type: string) => {
		switch (type.toUpperCase()) {
			case "LEAVE":
				return "bg-blue-50 text-blue-700 border-blue-200";
			case "EXPENSE":
				return "bg-purple-50 text-purple-700 border-purple-200";
			case "BENEFIT":
				return "bg-teal-50 text-teal-700 border-teal-200";
			default:
				return "bg-slate-50 text-slate-600 border-slate-200";
		}
	};

	const getRecommendationBadge = (rec?: string | null) => {
		if (!rec) return null;
		switch (rec.toUpperCase()) {
			case "APPROVE":
				return "bg-emerald-100 text-emerald-800 border-emerald-300";
			case "REJECT":
				return "bg-red-100 text-red-800 border-red-300";
			default:
				return "bg-amber-100 text-amber-800 border-amber-300";
		}
	};

	return (
		<div className="min-h-[calc(100vh-65px)] bg-slate-50 text-slate-900 p-4 sm:p-8 font-sans">
			<div className="max-w-7xl mx-auto space-y-6">
				{/* Top Header */}
				<div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
					<div>
						<h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">HR Request Dashboard</h1>
						<p className="text-sm text-slate-500 mt-1">Review policy rules, AI recommendations, and process employee requests.</p>
					</div>
					<button
						onClick={fetchRequests}
						disabled={loading}
						className="self-start sm:self-auto px-4 py-2 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
					>
						<svg className={`w-4 h-4 text-indigo-600 ${loading ? "animate-spin" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth="2"
								d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
							/>
						</svg>
						<span>Refresh</span>
					</button>
				</div>

				{/* Filters bar */}
				<div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm grid grid-cols-1 sm:grid-cols-3 gap-4">
					<div>
						<label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Request Type</label>
						<select
							value={selectedType}
							onChange={(e) => {
								setSelectedType(e.target.value);
								setPage(1);
							}}
							className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						>
							<option value="">All Types</option>
							<option value="LEAVE">Leave Request</option>
							<option value="EXPENSE">Expense Claim</option>
							<option value="BENEFIT">Health / Benefit Claim</option>
						</select>
					</div>

					<div>
						<label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Status</label>
						<select
							value={selectedStatus}
							onChange={(e) => {
								setSelectedStatus(e.target.value);
								setPage(1);
							}}
							className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						>
							<option value="">All Statuses</option>
							<option value="SUBMITTED">Submitted</option>
							<option value="PENDING_REVIEW">Pending Review</option>
							<option value="APPROVED">Approved</option>
							<option value="REJECTED">Rejected</option>
							<option value="CANCELLED">Cancelled</option>
						</select>
					</div>

					<div>
						<label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Search Employee Number</label>
						<input
							type="text"
							placeholder="e.g. EMP-0001"
							value={searchEmployee}
							onChange={(e) => {
								setSearchEmployee(e.target.value);
								setPage(1);
							}}
							className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						/>
					</div>
				</div>

				{/* Global Error Alert */}
				{error && (
					<div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-sm flex items-center justify-between">
						<div className="flex items-center space-x-2">
							<span>⚠️</span>
							<span>{error}</span>
						</div>
						<button
							onClick={fetchRequests}
							className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-800 text-xs font-semibold rounded-lg transition"
						>
							Retry
						</button>
					</div>
				)}

				{/* Requests Table */}
				<div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
					{loading ? (
						<div className="p-12 text-center text-slate-500 space-y-3">
							<svg className="animate-spin h-8 w-8 mx-auto text-indigo-600" fill="none" viewBox="0 0 24 24">
								<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
								<path
									className="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								></path>
							</svg>
							<div>Fetching request records...</div>
						</div>
					) : requests.length === 0 ? (
						<div className="p-12 text-center text-slate-500">No HR requests found matching your filter criteria.</div>
					) : (
						<>
							<div className="overflow-x-auto">
								<table className="w-full text-left text-sm text-slate-700">
									<thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
										<tr>
											<th className="py-3.5 px-4">Request Ref</th>
											<th className="py-3.5 px-4">Requester</th>
											<th className="py-3.5 px-4">Type</th>
											<th className="py-3.5 px-4">Requested Time</th>
											<th className="py-3.5 px-4">Status Updated Time</th>
											<th className="py-3.5 px-4">Title / Description</th>
											<th className="py-3.5 px-4">Attachment</th>
											<th className="py-3.5 px-4">Status</th>
											<th className="py-3.5 px-4 text-right">Actions</th>
										</tr>
									</thead>
									<tbody className="divide-y divide-slate-100">
										{requests.map((req) => (
											<tr key={req.request_id} className="hover:bg-slate-50/80 transition">
												<td className="py-3.5 px-4 font-mono text-xs font-semibold text-slate-900">{req.request_number}</td>

												<td className="py-3.5 px-4">
													<div className="font-semibold text-slate-900">{req.employee_name}</div>
													<div className="text-xs text-slate-500">
														{req.employee_number} • {req.department}
													</div>
												</td>

												<td className="py-3.5 px-4">
													<span
														className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getTypeBadge(req.request_type)}`}
													>
														{req.request_type}
													</span>
												</td>

												<td className="py-3.5 px-4 text-xs font-medium text-slate-600">{new Date(req.submitted_at).toLocaleString()}</td>

												<td className="py-3.5 px-4 text-xs font-medium text-slate-600">
													{req.updated_at ? new Date(req.updated_at).toLocaleString() : "—"}
												</td>

												<td className="py-3.5 px-4 max-w-xs">
													<div className="font-medium text-slate-900 truncate">{req.title}</div>
													{req.description && <div className="text-xs text-slate-500 truncate mt-0.5">{req.description}</div>}
												</td>

												<td className="py-3.5 px-4">
													{req.blob_url ? (
														<a
															href={req.blob_url}
															target="_blank"
															rel="noopener noreferrer"
															className="inline-flex items-center space-x-1 text-xs text-indigo-600 font-semibold hover:underline bg-indigo-50 px-2 py-1 rounded border border-indigo-200"
														>
															<span>📎 Attachment</span>
														</a>
													) : (
														<span className="text-xs text-slate-400">—</span>
													)}
												</td>

												<td className="py-3.5 px-4">
													<span
														className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(req.status)}`}
													>
														{req.status}
													</span>
												</td>

												<td className="py-3.5 px-4 text-right">
													<button
														onClick={() => {
															setSelectedRequest(req);
															setActionFeedback(null);
															setActionReason("");
															setActionReasonError(null);
															setConfirmAction(null);
														}}
														className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 rounded-lg border border-slate-200 transition"
													>
														Review & Process
													</button>
												</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>

							{/* Pagination Controls */}
							<div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
								<div>
									Showing page <span className="font-bold text-slate-900">{page}</span> of{" "}
									<span className="font-bold text-slate-900">{totalPages}</span> ({totalCount} total requests)
								</div>
								<div className="flex space-x-2">
									<button
										disabled={page <= 1}
										onClick={() => setPage((prev) => Math.max(1, prev - 1))}
										className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition"
									>
										Previous
									</button>
									<button
										disabled={page >= totalPages}
										onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
										className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition"
									>
										Next
									</button>
								</div>
							</div>
						</>
					)}
				</div>
			</div>

			{/* Request Details & Action Modal */}
			{selectedRequest && (
				<div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
					<div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl overflow-y-auto max-h-[90vh]">
						<div className="flex justify-between items-start border-b border-slate-100 pb-4">
							<div>
								<div className="flex items-center space-x-3">
									<h2 className="text-xl font-bold text-slate-900">{selectedRequest.request_number}</h2>
									<span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getTypeBadge(selectedRequest.request_type)}`}>
										{selectedRequest.request_type}
									</span>
									<span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(selectedRequest.status)}`}>
										{selectedRequest.status}
									</span>
								</div>
								<p className="text-xs text-slate-500 mt-1">Submitted on {new Date(selectedRequest.submitted_at).toLocaleString()}</p>
							</div>
							<button onClick={() => setSelectedRequest(null)} className="text-slate-400 hover:text-slate-700 text-lg font-bold p-1">
								✕
							</button>
						</div>

						{/* Requester Info */}
						<div className="bg-slate-50 p-4 rounded-xl border border-slate-200 grid grid-cols-2 gap-3 text-xs">
							<div>
								<span className="text-slate-500 block">Requester Name</span>
								<span className="font-semibold text-slate-800">{selectedRequest.employee_name}</span>
							</div>
							<div>
								<span className="text-slate-500 block">Employee Number</span>
								<span className="font-semibold text-slate-800">{selectedRequest.employee_number}</span>
							</div>
							<div>
								<span className="text-slate-500 block">Department</span>
								<span className="font-semibold text-slate-800">{selectedRequest.department}</span>
							</div>
							<div>
								<span className="text-slate-500 block">Eligibility Result</span>
								<span className="font-semibold text-indigo-700">{selectedRequest.eligibility_result || "N/A"}</span>
							</div>
						</div>

						{/* Title & Description & Attachment */}
						<div className="space-y-2">
							<h3 className="text-sm font-semibold text-slate-800">Request Summary</h3>
							<div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 space-y-2">
								<div className="font-bold text-slate-900 text-sm">{selectedRequest.title}</div>
								{selectedRequest.description && <div>{selectedRequest.description}</div>}
								{selectedRequest.blob_url && (
									<div className="pt-1">
										<a
											href={selectedRequest.blob_url}
											target="_blank"
											rel="noopener noreferrer"
											className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-lg text-xs font-semibold hover:bg-indigo-100 transition"
										>
											<span>📎 Open Attachment Document</span>
										</a>
									</div>
								)}
							</div>
						</div>

						{/* AI Recommendation */}
						{selectedRequest.reasoning_summary && (
							<div className="space-y-2">
								<h3 className="text-sm font-semibold text-slate-800 flex items-center space-x-2">
									<span className="text-indigo-700 font-bold">AI Recommendation</span>
									{selectedRequest.recommendation && (
										<span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRecommendationBadge(selectedRequest.recommendation)}`}>
											{selectedRequest.recommendation}
										</span>
									)}
								</h3>
								<div className="p-4 bg-indigo-50/60 border border-indigo-200 rounded-xl text-xs text-indigo-950 whitespace-pre-wrap leading-relaxed">
									{selectedRequest.reasoning_summary}
								</div>
							</div>
						)}

						{/* Action Feedback Toast */}
						{actionFeedback && (
							<div
								className={`p-3.5 rounded-xl text-xs border flex items-center justify-between ${
									actionFeedback.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-red-50 border-red-200 text-red-800"
								}`}
							>
								<div className="flex items-center space-x-2">
									<span>{actionFeedback.type === "success" ? "✅" : "⚠️"}</span>
									<span>{actionFeedback.message}</span>
								</div>
								<button onClick={() => setActionFeedback(null)} className="text-xs font-bold px-2">
									✕
								</button>
							</div>
						)}

						{/* Confirmation Alert Box */}
						{confirmAction && (
							<div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-3">
								<div className="text-xs text-amber-900 font-semibold flex items-center space-x-2">
									<span>⚠️ Confirm Action:</span>
									<span>
										Are you sure you want to {confirmAction.toUpperCase()} request {selectedRequest.request_number}?
									</span>
								</div>
								<div className="flex space-x-2 justify-end">
									<button
										onClick={() => setConfirmAction(null)}
										className="px-3 py-1.5 bg-white border border-slate-200 text-xs font-semibold text-slate-700 rounded-lg hover:bg-slate-50 transition"
									>
										Cancel
									</button>
									<button
										onClick={handleExecuteStatusUpdate}
										disabled={actionLoading}
										className={`px-4 py-1.5 text-xs font-bold text-white rounded-lg transition ${
											confirmAction === "accept" ? "bg-emerald-600 hover:bg-emerald-500" : "bg-red-600 hover:bg-red-500"
										}`}
									>
										{actionLoading ? "Processing..." : `Yes, ${confirmAction === "accept" ? "Approve" : "Reject"}`}
									</button>
								</div>
							</div>
						)}

						{/* Action Controls for HR */}
						{selectedRequest.status !== "APPROVED" && selectedRequest.status !== "REJECTED" && selectedRequest.status !== "CANCELLED" ? (
							<div className="space-y-3 border-t border-slate-100 pt-4">
								<div>
									<label className="block text-xs font-semibold text-slate-700 mb-1">Decision Notes / Reason:</label>
									<textarea
										rows={2}
										value={actionReason}
										onChange={(e) => {
											setActionReason(e.target.value);
											if (actionReasonError) setActionReasonError(null);
										}}
										placeholder="Enter approval note or rejection justification..."
										className={`w-full bg-slate-50 border rounded-xl p-3 text-xs text-slate-900 placeholder-slate-400 focus:outline-none transition ${
											actionReasonError ? "border-red-500 focus:ring-2 focus:ring-red-500/20" : "border-slate-200 focus:ring-2 focus:ring-indigo-500"
										}`}
									/>
									{actionReasonError && (
										<p className="mt-1 text-xs text-red-600 flex items-center space-x-1">
											<span>⚠️</span>
											<span>{actionReasonError}</span>
										</p>
									)}
								</div>

								{!confirmAction && (
									<div className="flex space-x-3">
										<button
											onClick={() => handleInitiateAction("accept")}
											disabled={actionLoading}
											className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-sm disabled:opacity-50 transition"
										>
											Approve Request
										</button>

										<button
											onClick={() => handleInitiateAction("reject")}
											disabled={actionLoading}
											className="flex-1 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold shadow-sm disabled:opacity-50 transition"
										>
											Reject Request
										</button>
									</div>
								)}
							</div>
						) : (
							<div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 text-center font-medium">
								🔒 This request has been finalized as <span className="font-bold text-slate-900">{selectedRequest.status}</span>.
							</div>
						)}
					</div>
				</div>
			)}
		</div>
	);
};
