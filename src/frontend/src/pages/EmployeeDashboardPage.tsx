import React, { useCallback, useEffect, useState } from "react";
import type { RequestSummaryItem } from "../types/request";
import { cancelRequestApi, getRequestsApi } from "../services/api";

export const EmployeeDashboardPage: React.FC = () => {
	const [requests, setRequests] = useState<RequestSummaryItem[]>([]);
	const [loading, setLoading] = useState<boolean>(true);
	const [error, setError] = useState<string | null>(null);

	// Filters
	const [selectedType, setSelectedType] = useState<string>("");
	const [selectedStatus, setSelectedStatus] = useState<string>("");

	// Pagination
	const [page, setPage] = useState<number>(1);
	const [pageSize] = useState<number>(10);
	const [totalPages, setTotalPages] = useState<number>(1);
	const [totalCount, setTotalCount] = useState<number>(0);

	// Modal Details & Cancellation Form State
	const [selectedRequest, setSelectedRequest] = useState<RequestSummaryItem | null>(null);
	const [cancelModalOpen, setCancelModalOpen] = useState<boolean>(false);
	const [cancelReason, setCancelReason] = useState<string>("");
	const [cancelReasonError, setCancelReasonError] = useState<string | null>(null);
	const [cancelLoading, setCancelLoading] = useState<boolean>(false);
	const [cancelFeedback, setCancelFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

	const fetchRequests = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const res = await getRequestsApi({
				request_type: selectedType || undefined,
				status: selectedStatus || undefined,
				my_requests_only: true,
				page,
				page_size: pageSize,
			});

			if (res.is_success && res.payload) {
				setRequests(res.payload.requests || []);
				setTotalPages(res.payload.total_pages || 1);
				setTotalCount(res.payload.total_count || 0);
			} else {
				setError(res.message || "Failed to load request list.");
			}
		} catch (err: unknown) {
			setError((err as Error).message || "An error occurred while fetching requests.");
		} finally {
			setLoading(false);
		}
	}, [selectedType, selectedStatus, page, pageSize]);

	useEffect(() => {
		fetchRequests();
	}, [fetchRequests]);

	const handleOpenCancelModal = (req: RequestSummaryItem) => {
		setSelectedRequest(req);
		setCancelReason("");
		setCancelReasonError(null);
		setCancelFeedback(null);
		setCancelModalOpen(true);
	};

	const handleExecuteCancel = async () => {
		if (!selectedRequest) return;

		if (selectedRequest.status === "APPROVED" || selectedRequest.status === "REJECTED" || selectedRequest.status === "CANCELLED") {
			setCancelFeedback({
				type: "error",
				message: `Requests in '${selectedRequest.status}' state cannot be cancelled.`,
			});
			return;
		}

		if (!cancelReason.trim()) {
			setCancelReasonError("Please provide a reason for cancelling your request.");
			return;
		}

		setCancelLoading(true);
		setCancelReasonError(null);
		setCancelFeedback(null);

		try {
			const res = await cancelRequestApi({
				request_id: selectedRequest.request_id,
				reason: cancelReason.trim(),
			});

			if (res.is_success) {
				setCancelFeedback({
					type: "success",
					message: `Request ${selectedRequest.request_number} has been cancelled.`,
				});
				setCancelReason("");
				fetchRequests();
				setTimeout(() => {
					setCancelModalOpen(false);
					setSelectedRequest(null);
				}, 1500);
			} else {
				setCancelFeedback({
					type: "error",
					message: res.message || res.error || "Failed to cancel request.",
				});
			}
		} catch (err: unknown) {
			setCancelFeedback({
				type: "error",
				message: (err as Error).message || "Failed to submit request cancellation.",
			});
		} finally {
			setCancelLoading(false);
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

	return (
		<div className="min-h-[calc(100vh-65px)] bg-slate-50 text-slate-900 p-4 sm:p-8 font-sans">
			<div className="max-w-7xl mx-auto space-y-6">
				{/* Header */}
				<div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
					<div>
						<h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">My HR Requests</h1>
						<p className="text-sm text-slate-500 mt-1">Track the status of your leave applications, expense claims, and health benefit requests.</p>
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

				{/* Filters Bar */}
				<div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm grid grid-cols-1 sm:grid-cols-2 gap-4">
					<div>
						<label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Request Type</label>
						<select
							value={selectedType}
							onChange={(e) => {
								setSelectedType(e.target.value);
								setPage(1);
							}}
							className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
							className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						>
							<option value="">All Statuses</option>
							<option value="SUBMITTED">Submitted</option>
							<option value="PENDING_REVIEW">Pending Review</option>
							<option value="APPROVED">Approved</option>
							<option value="REJECTED">Rejected</option>
							<option value="CANCELLED">Cancelled</option>
						</select>
					</div>
				</div>

				{/* Error State */}
				{error && (
					<div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-sm flex items-center justify-between">
						<span>⚠️ {error}</span>
						<button onClick={fetchRequests} className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-800 text-xs font-semibold rounded-lg">
							Retry
						</button>
					</div>
				)}

				{/* Table */}
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
							<div>Loading your HR requests...</div>
						</div>
					) : requests.length === 0 ? (
						<div className="p-12 text-center text-slate-500">No requests found matching your filter criteria.</div>
					) : (
						<>
							<div className="overflow-x-auto">
								<table className="w-full text-left text-sm text-slate-700">
									<thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
										<tr>
											<th className="py-3.5 px-4">Request Type</th>
											<th className="py-3.5 px-4">Requested Time</th>
											<th className="py-3.5 px-4">Description</th>
											<th className="py-3.5 px-4">Status</th>
											<th className="py-3.5 px-4">Status Updated Time</th>
											<th className="py-3.5 px-4 text-right">Action</th>
										</tr>
									</thead>
									<tbody className="divide-y divide-slate-100">
										{requests.map((req) => (
											<tr key={req.request_id} className="hover:bg-slate-50/80 transition">
												<td className="py-3.5 px-4">
													<div className="flex items-center space-x-2">
														<span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getTypeBadge(req.request_type)}`}>
															{req.request_type}
														</span>
														<span className="font-mono text-xs text-slate-500 font-semibold">{req.request_number}</span>
													</div>
												</td>

												<td className="py-3.5 px-4 text-slate-600 text-xs font-medium">{new Date(req.submitted_at).toLocaleString()}</td>

												<td className="py-3.5 px-4 max-w-xs">
													<div className="font-semibold text-slate-900 truncate">{req.title}</div>
													{req.description && <div className="text-xs text-slate-500 truncate mt-0.5">{req.description}</div>}
												</td>

												<td className="py-3.5 px-4">
													<span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(req.status)}`}>{req.status}</span>
												</td>

												<td className="py-3.5 px-4 text-slate-600 text-xs font-medium">
													{req.updated_at ? new Date(req.updated_at).toLocaleString() : "—"}
												</td>

												<td className="py-3.5 px-4 text-right space-x-2">
													<button
														onClick={() => setSelectedRequest(req)}
														className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 rounded-lg transition"
													>
														Details
													</button>
													{req.status !== "APPROVED" && req.status !== "REJECTED" && req.status !== "CANCELLED" && (
														<button
															onClick={() => handleOpenCancelModal(req)}
															className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 text-xs font-semibold rounded-lg transition"
														>
															Cancel Request
														</button>
													)}
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

			{/* Details Modal */}
			{selectedRequest && !cancelModalOpen && (
				<div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
					<div className="bg-white border border-slate-200 rounded-2xl max-w-xl w-full p-6 space-y-6 shadow-xl">
						<div className="flex justify-between items-start border-b border-slate-100 pb-4">
							<div>
								<div className="flex items-center space-x-2">
									<h2 className="text-lg font-bold text-slate-900">{selectedRequest.request_number}</h2>
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

						<div className="space-y-3 text-xs">
							<div>
								<span className="text-slate-500 font-medium">Request Title:</span>
								<div className="font-bold text-slate-900 text-sm mt-0.5">{selectedRequest.title}</div>
							</div>
							{selectedRequest.description && (
								<div>
									<span className="text-slate-500 font-medium">Description / Details:</span>
									<div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 mt-1">{selectedRequest.description}</div>
								</div>
							)}
							{selectedRequest.blob_url && (
								<div>
									<span className="text-slate-500 font-medium">Attachment Preview:</span>
									<div className="mt-1">
										<a
											href={selectedRequest.blob_url}
											target="_blank"
											rel="noopener noreferrer"
											className="inline-flex items-center space-x-2 px-3 py-1.5 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-lg text-xs font-semibold hover:bg-indigo-100 transition"
										>
											<span>📎 View Attachment</span>
										</a>
									</div>
								</div>
							)}
							{(selectedRequest.decision_reason || selectedRequest.reasoning_summary) && (
								<div>
									<span className="text-slate-500 font-medium">Reason / Decision Note:</span>
									<div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 mt-1 font-medium leading-relaxed">
										{selectedRequest.decision_reason || selectedRequest.reasoning_summary}
									</div>
								</div>
							)}
						</div>

						<div className="flex justify-end pt-2 border-t border-slate-100">
							<button
								onClick={() => setSelectedRequest(null)}
								className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 rounded-xl transition"
							>
								Close
							</button>
						</div>
					</div>
				</div>
			)}

			{/* Employee Request Cancellation Form Modal */}
			{cancelModalOpen && selectedRequest && (
				<div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
					<div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
						<div className="flex justify-between items-start border-b border-slate-100 pb-3">
							<div>
								<h2 className="text-base font-bold text-slate-900">Request Cancellation Form</h2>
								<p className="text-xs text-slate-500 mt-0.5">Cancelling request {selectedRequest.request_number}</p>
							</div>
							<button onClick={() => setCancelModalOpen(false)} className="text-slate-400 hover:text-slate-700 font-bold p-1">
								✕
							</button>
						</div>

						{cancelFeedback && (
							<div
								className={`p-3 rounded-xl text-xs border ${
									cancelFeedback.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-red-50 border-red-200 text-red-800"
								}`}
							>
								{cancelFeedback.message}
							</div>
						)}

						<div className="space-y-3">
							<div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs">
								<div className="font-semibold text-slate-800">{selectedRequest.title}</div>
								<div className="text-slate-500 mt-0.5">Submitted: {new Date(selectedRequest.submitted_at).toLocaleDateString()}</div>
							</div>

							<div>
								<label className="block text-xs font-semibold text-slate-700 mb-1">
									Reason for Cancellation <span className="text-red-500">*</span>
								</label>
								<textarea
									rows={3}
									value={cancelReason}
									onChange={(e) => {
										setCancelReason(e.target.value);
										if (cancelReasonError) setCancelReasonError(null);
									}}
									placeholder="Explain why you are cancelling this request..."
									className={`w-full bg-slate-50 border rounded-xl p-3 text-xs text-slate-900 focus:outline-none transition ${
										cancelReasonError ? "border-red-500 focus:ring-2 focus:ring-red-500/20" : "border-slate-200 focus:ring-2 focus:ring-indigo-500"
									}`}
								/>
								{cancelReasonError && <p className="mt-1 text-xs text-red-600">⚠️ {cancelReasonError}</p>}
							</div>
						</div>

						<div className="flex space-x-3 pt-2">
							<button
								onClick={() => setCancelModalOpen(false)}
								disabled={cancelLoading}
								className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
							>
								Back
							</button>
							<button
								onClick={handleExecuteCancel}
								disabled={cancelLoading}
								className="flex-1 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold transition shadow-md shadow-red-600/20 disabled:opacity-50"
							>
								{cancelLoading ? "Cancelling..." : "Confirm Cancellation"}
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
};
