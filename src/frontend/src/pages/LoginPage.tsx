import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const LoginPage: React.FC = () => {
	const { login } = useAuth();
	const navigate = useNavigate();

	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");

	const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
	const [serverError, setServerError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	const validateInputs = (): boolean => {
		const errors: { email?: string; password?: string } = {};

		// Email validation
		const trimmedEmail = email.trim();
		if (!trimmedEmail) {
			errors.email = "Email address is required.";
		} else {
			const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
			if (!emailRegex.test(trimmedEmail)) {
				errors.email = "Please enter a valid email address (e.g., name@company.com).";
			}
		}

		// Password validation
		if (!password) {
			errors.password = "Password is required.";
		}

		setFieldErrors(errors);
		return Object.keys(errors).length === 0;
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setServerError(null);

		if (!validateInputs()) {
			return;
		}

		setLoading(true);
		try {
			const userProfile = await login(email.trim(), password);

			// Redirect based on user role using React Router
			if (userProfile.role === "HR_ADMIN") {
				navigate("/dashboard", { replace: true });
			} else {
				navigate("/chat", { replace: true });
			}
		} catch (err: unknown) {
			const message = (err as Error).message || "";

			if (message.includes("Failed to fetch") || message.includes("NetworkError") || message.includes("connection")) {
				setServerError(
					"Unable to connect to the backend server. Please verify that the backend API is running on port 9000 and PostgreSQL database is connected.",
				);
			} else {
				// Wrong email or password error
				setServerError("Incorrect email or password. Please verify your credentials and try again.");
				setFieldErrors({
					password: "Incorrect password or email.",
				});
			}
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100 font-sans">
			<div className="sm:mx-auto sm:w-full sm:max-w-md">
				<div className="flex justify-center items-center space-x-3">
					<div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-2xl shadow-xl shadow-indigo-500/30">
						HR
					</div>
				</div>
				<h2 className="mt-4 text-center text-3xl font-extrabold text-white tracking-tight">HR Platform</h2>
				<p className="mt-2 text-center text-sm text-slate-400">AI-Powered Request Management & Decision Support</p>
			</div>

			<div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
				<div className="bg-slate-900/90 backdrop-blur-md py-8 px-4 shadow-2xl shadow-black/50 sm:rounded-2xl border border-slate-800 sm:px-10">
					{serverError && (
						<div className="mb-6 bg-red-500/10 border border-red-500/40 text-red-300 px-4 py-3 rounded-xl text-sm flex items-start space-x-3">
							<svg className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<div className="flex-1">
								<div className="font-semibold text-red-400">Authentication Warning</div>
								<div className="text-xs text-red-300/90 mt-0.5">{serverError}</div>
							</div>
						</div>
					)}

					<form className="space-y-5" onSubmit={handleSubmit} noValidate>
						<div>
							<label className="block text-sm font-medium text-slate-300 mb-1">
								Email Address <span className="text-red-400">*</span>
							</label>
							<input
								type="email"
								value={email}
								onChange={(e) => {
									setEmail(e.target.value);
									if (fieldErrors.email) setFieldErrors((prev) => ({ ...prev, email: undefined }));
								}}
								placeholder="e.g. employee@company.com"
								className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 focus:outline-none transition text-sm ${
									fieldErrors.email
										? "border-red-500 focus:ring-2 focus:ring-red-500/50"
										: "border-slate-800 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
								}`}
							/>
							{fieldErrors.email && (
								<p className="mt-1 text-xs text-red-400 flex items-center space-x-1">
									<span>⚠️</span>
									<span>{fieldErrors.email}</span>
								</p>
							)}
						</div>

						<div>
							<label className="block text-sm font-medium text-slate-300 mb-1">
								Password <span className="text-red-400">*</span>
							</label>
							<input
								type="password"
								value={password}
								onChange={(e) => {
									setPassword(e.target.value);
									if (fieldErrors.password) setFieldErrors((prev) => ({ ...prev, password: undefined }));
								}}
								placeholder="••••••••"
								className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 focus:outline-none transition text-sm ${
									fieldErrors.password
										? "border-red-500 focus:ring-2 focus:ring-red-500/50"
										: "border-slate-800 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
								}`}
							/>
							{fieldErrors.password && (
								<p className="mt-1 text-xs text-red-400 flex items-center space-x-1">
									<span>⚠️</span>
									<span>{fieldErrors.password}</span>
								</p>
							)}
						</div>

						<div className="pt-2">
							<button
								type="submit"
								disabled={loading}
								className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg shadow-indigo-600/30 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
							>
								{loading ? (
									<span className="flex items-center space-x-2">
										<svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
											<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
											<path
												className="opacity-75"
												fill="currentColor"
												d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
											></path>
										</svg>
										<span>Authenticating...</span>
									</span>
								) : (
									"Sign In"
								)}
							</button>
						</div>
					</form>
				</div>
			</div>
		</div>
	);
};
