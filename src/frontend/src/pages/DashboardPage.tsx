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
			});

			if (res.is_success && res.payload) {
				setRequests(res.payload.requests || []);
			} else {
				setError(res.message || "Failed to load HR request list.");
			}
		} catch (err: unknown) {
			setError((err as Error).message || "An error occurred while fetching HR requests.");
		} finally {
			setLoading(false);
		}
	}, [selectedType, selectedStatus, searchEmployee]);

	useEffect(() => {
		fetchRequests();
	}, [fetchRequests]);

	const handleInitiateAction = (action: "accept" | "reject") => {
		setActionReasonError(null);
		setActionFeedback(null);

		if (!selectedRequest) return;

		// Check if request is already finalized
		if (selectedRequest.status === "APPROVED" || selectedRequest.status === "REJECTED") {
			setActionFeedback({
				type: "error",
				message: `This request is already ${selectedRequest.status} and cannot be modified further.`,
			});
			return;
		}

		// Require reason for rejection
		if (action === "reject" && !actionReason.trim()) {
			setActionReasonError("A rejection reason is required so the employee understands why their request was declined.");
			return;
		}

		// Trigger confirmation prompt
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

				// Refresh background table list
				fetchRequests();

				// Update active modal request status
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
				return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
			case "REJECTED":
				return "bg-red-500/10 text-red-400 border-red-500/30";
			case "PENDING_REVIEW":
			case "SUBMITTED":
				return "bg-amber-500/10 text-amber-400 border-amber-500/30";
			default:
				return "bg-slate-500/10 text-slate-400 border-slate-500/30";
		}
	};

	const getTypeBadge = (type: string) => {
		switch (type.toUpperCase()) {
			case "LEAVE":
				return "bg-blue-500/10 text-blue-400 border-blue-500/30";
			case "EXPENSE":
				return "bg-purple-500/10 text-purple-400 border-purple-500/30";
			case "BENEFIT":
				return "bg-teal-500/10 text-teal-400 border-teal-500/30";
			default:
				return "bg-slate-500/10 text-slate-400 border-slate-500/30";
		}
	};

	const getRecommendationBadge = (rec?: string | null) => {
		if (!rec) return null;
		switch (rec.toUpperCase()) {
			case "APPROVE":
				return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
			case "REJECT":
				return "bg-red-500/20 text-red-300 border-red-500/40";
			default:
				return "bg-amber-500/20 text-amber-300 border-amber-500/40";
		}
	};

	return (
		<div className="min-h-[calc(100vh-65px)] bg-slate-950 text-slate-100 p-4 sm:p-8 font-sans">
			<div className="max-w-7xl mx-auto space-y-6">
				{/* Top Header */}
				<div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
					<div>
						<h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">HR Request Dashboard</h1>
						<p className="text-sm text-slate-400 mt-1">Review policy rules, AI decision support, and process employee requests.</p>
					</div>
					<button
						onClick={fetchRequests}
						disabled={loading}
						className="self-start sm:self-auto px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-sm font-medium transition flex items-center space-x-2 disabled:opacity-50"
					>
						<svg className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
				<div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl grid grid-cols-1 sm:grid-cols-3 gap-4">
					<div>
						<label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Request Type</label>
						<select
							value={selectedType}
							onChange={(e) => setSelectedType(e.target.value)}
							className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
						>
							<option value="">All Types</option>
							<option value="LEAVE">Leave Request</option>
							<option value="EXPENSE">Expense Claim</option>
							<option value="BENEFIT">Health / Benefit Claim</option>
						</select>
					</div>

					<div>
						<label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Status</label>
						<select
							value={selectedStatus}
							onChange={(e) => setSelectedStatus(e.target.value)}
							className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
						>
							<option value="">All Statuses</option>
							<option value="SUBMITTED">Submitted</option>
							<option value="PENDING_REVIEW">Pending Review</option>
							<option value="APPROVED">Approved</option>
							<option value="REJECTED">Rejected</option>
						</select>
					</div>

					<div>
						<label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Search Employee Number</label>
						<input
							type="text"
							placeholder="e.g. EMP-0001"
							value={searchEmployee}
							onChange={(e) => setSearchEmployee(e.target.value)}
							className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						/>
					</div>
				</div>

				{/* Global Error Alert */}
				{error && (
					<div className="bg-red-500/10 border border-red-500/40 text-red-300 p-4 rounded-2xl text-sm flex items-center justify-between">
						<div className="flex items-center space-x-2">
							<span>⚠️</span>
							<span>{error}</span>
						</div>
						<button
							onClick={fetchRequests}
							className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-200 text-xs font-semibold rounded-lg transition"
						>
							Retry
						</button>
					</div>
				)}

				{/* Requests Table */}
				<div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
					{loading ? (
						<div className="p-12 text-center text-slate-400 space-y-3">
							<svg className="animate-spin h-8 w-8 mx-auto text-indigo-500" fill="none" viewBox="0 0 24 24">
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
						<div className="p-12 text-center text-slate-400">No HR requests found matching your filter criteria.</div>
					) : (
						<div className="overflow-x-auto">
							<table className="w-full text-left text-sm text-slate-300">
								<thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
									<tr>
										<th className="py-3.5 px-4">Request Ref</th>
										<th className="py-3.5 px-4">Requester</th>
										<th className="py-3.5 px-4">Type</th>
										<th className="py-3.5 px-4">Title / Description</th>
										<th className="py-3.5 px-4">AI Rec</th>
										<th className="py-3.5 px-4">Status</th>
										<th className="py-3.5 px-4 text-right">Actions</th>
									</tr>
								</thead>
								<tbody className="divide-y divide-slate-800/60">
									{requests.map((req) => (
										<tr key={req.request_id} className="hover:bg-slate-800/40 transition">
											<td className="py-3.5 px-4 font-mono text-xs font-semibold text-slate-200">
												{req.request_number}
												<div className="text-[10px] text-slate-500 font-sans">{new Date(req.submitted_at).toLocaleDateString()}</div>
											</td>

											<td className="py-3.5 px-4">
												<div className="font-semibold text-slate-100">{req.employee_name}</div>
												<div className="text-xs text-slate-400">
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

											<td className="py-3.5 px-4 max-w-xs">
												<div className="font-medium text-slate-200 truncate">{req.title}</div>
												{req.description && <div className="text-xs text-slate-400 truncate mt-0.5">{req.description}</div>}
											</td>

											<td className="py-3.5 px-4">
												{req.recommendation ? (
													<span
														className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${getRecommendationBadge(req.recommendation)}`}
													>
														{req.recommendation}
													</span>
												) : (
													<span className="text-xs text-slate-500">—</span>
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
													className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 rounded-lg border border-slate-700 transition"
												>
													Review & Process
												</button>
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					)}
				</div>
			</div>

			{/* Request Details & Action Modal */}
			{selectedRequest && (
				<div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
					<div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl overflow-y-auto max-h-[90vh]">
						<div className="flex justify-between items-start border-b border-slate-800 pb-4">
							<div>
								<div className="flex items-center space-x-3">
									<h2 className="text-xl font-bold text-white">{selectedRequest.request_number}</h2>
									<span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getTypeBadge(selectedRequest.request_type)}`}>
										{selectedRequest.request_type}
									</span>
									<span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(selectedRequest.status)}`}>
										{selectedRequest.status}
									</span>
								</div>
								<p className="text-xs text-slate-400 mt-1">Submitted on {new Date(selectedRequest.submitted_at).toLocaleString()}</p>
							</div>
							<button onClick={() => setSelectedRequest(null)} className="text-slate-400 hover:text-white text-lg font-bold p-1">
								✕
							</button>
						</div>

						{/* Requester Info */}
						<div className="bg-slate-950 p-4 rounded-xl border border-slate-800 grid grid-cols-2 gap-3 text-xs">
							<div>
								<span className="text-slate-500 block">Requester Name</span>
								<span className="font-semibold text-slate-200">{selectedRequest.employee_name}</span>
							</div>
							<div>
								<span className="text-slate-500 block">Employee Number</span>
								<span className="font-semibold text-slate-200">{selectedRequest.employee_number}</span>
							</div>
							<div>
								<span className="text-slate-500 block">Department</span>
								<span className="font-semibold text-slate-200">{selectedRequest.department}</span>
							</div>
							<div>
								<span className="text-slate-500 block">Eligibility Result</span>
								<span className="font-semibold text-indigo-400">{selectedRequest.eligibility_result || "N/A"}</span>
							</div>
						</div>

						{/* Title & Description */}
						<div className="space-y-2">
							<h3 className="text-sm font-semibold text-slate-300">Request Summary</h3>
							<div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-300 space-y-1">
								<div className="font-bold text-white text-sm">{selectedRequest.title}</div>
								{selectedRequest.description && <div>{selectedRequest.description}</div>}
							</div>
						</div>

						{/* AI Decision Support & Reasoning */}
						{selectedRequest.reasoning_summary && (
							<div className="space-y-2">
								<h3 className="text-sm font-semibold text-slate-300 flex items-center space-x-2">
									<span className="text-indigo-400 font-bold">🤖 AI Decision Support & Policy Audit</span>
									{selectedRequest.recommendation && (
										<span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRecommendationBadge(selectedRequest.recommendation)}`}>
											{selectedRequest.recommendation}
										</span>
									)}
								</h3>
								<div className="p-4 bg-indigo-950/30 border border-indigo-500/30 rounded-xl text-xs text-indigo-200 whitespace-pre-wrap leading-relaxed">
									{selectedRequest.reasoning_summary}
								</div>
							</div>
						)}

						{/* Action Feedback Toast */}
						{actionFeedback && (
							<div
								className={`p-3.5 rounded-xl text-xs border flex items-center justify-between ${
									actionFeedback.type === "success"
										? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
										: "bg-red-500/10 border-red-500/30 text-red-300"
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
							<div className="p-4 bg-slate-950 border border-amber-500/40 rounded-xl space-y-3">
								<div className="text-xs text-amber-300 font-semibold flex items-center space-x-2">
									<span>⚠️ Confirm Action:</span>
									<span>
										Are you sure you want to {confirmAction.toUpperCase()} request {selectedRequest.request_number}?
									</span>
								</div>
								<div className="flex space-x-2 justify-end">
									<button
										onClick={() => setConfirmAction(null)}
										className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 rounded-lg transition"
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
						{selectedRequest.status !== "APPROVED" && selectedRequest.status !== "REJECTED" ? (
							<div className="space-y-3 border-t border-slate-800 pt-4">
								<div>
									<label className="block text-xs font-semibold text-slate-300 mb-1">Decision Notes / Reason:</label>
									<textarea
										rows={2}
										value={actionReason}
										onChange={(e) => {
											setActionReason(e.target.value);
											if (actionReasonError) setActionReasonError(null);
										}}
										placeholder="Enter approval note or rejection justification..."
										className={`w-full bg-slate-950 border rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none transition ${
											actionReasonError ? "border-red-500 focus:ring-2 focus:ring-red-500/50" : "border-slate-800 focus:ring-2 focus:ring-indigo-500"
										}`}
									/>
									{actionReasonError && (
										<p className="mt-1 text-xs text-red-400 flex items-center space-x-1">
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
											className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/20 disabled:opacity-50 transition"
										>
											Approve Request
										</button>

										<button
											onClick={() => handleInitiateAction("reject")}
											disabled={actionLoading}
											className="flex-1 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-red-600/20 disabled:opacity-50 transition"
										>
											Reject Request
										</button>
									</div>
								)}
							</div>
						) : (
							<div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-400 text-center font-medium">
								🔒 This request has been finalized as <span className="font-bold text-white">{selectedRequest.status}</span>.
							</div>
						)}
					</div>
				</div>
			)}
		</div>
	);
};
