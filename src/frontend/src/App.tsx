import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginPage } from "./pages/LoginPage";
import { ChatbotPage } from "./pages/ChatbotPage";
import { DashboardPage } from "./pages/DashboardPage";

// Protected Route Guard for logged-in users
const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: string[] }> = ({ children, allowedRoles }) => {
	const { user, isAuthenticated, isLoading } = useAuth();
	const location = useLocation();
	const [accessWarning, setAccessWarning] = useState<string | null>(null);

	if (isLoading) {
		return (
			<div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
				<div className="flex items-center space-x-3">
					<svg className="animate-spin h-6 w-6 text-indigo-500" fill="none" viewBox="0 0 24 24">
						<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
						<path
							className="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					<span className="text-sm font-medium text-slate-300">Checking session credentials...</span>
				</div>
			</div>
		);
	}

	if (!isAuthenticated || !user) {
		return <Navigate to="/login" state={{ from: location }} replace />;
	}

	if (allowedRoles && !allowedRoles.includes(user.role)) {
		return <Navigate to="/chat" state={{ warning: "Access denied. The HR Dashboard is restricted to HR Administrators." }} replace />;
	}

	return <>{children}</>;
};

// Layout Header wrapper
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const { user, logout } = useAuth();
	const navigate = useNavigate();
	const location = useLocation();

	const handleLogout = () => {
		logout();
		navigate("/login", { replace: true });
	};

	return (
		<div className="min-h-screen bg-slate-950 flex flex-col font-sans">
			{/* Navigation Header */}
			<header className="h-[65px] bg-slate-900 border-b border-slate-800 px-4 sm:px-8 flex items-center justify-between z-10">
				<div className="flex items-center space-x-6">
					<div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate("/")}>
						<div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-md">
							HR
						</div>
						<span className="font-extrabold text-white text-base tracking-tight hidden sm:inline">HR Platform</span>
					</div>

					{/* Navigation Links using React Router */}
					<nav className="flex space-x-2">
						<button
							onClick={() => navigate("/chat")}
							className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
								location.pathname === "/chat"
									? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
									: "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
							}`}
						>
							💬 AI Assistant
						</button>

						{user?.role === "HR_ADMIN" && (
							<button
								onClick={() => navigate("/dashboard")}
								className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
									location.pathname === "/dashboard"
										? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
										: "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
								}`}
							>
								📊 HR Dashboard
							</button>
						)}
					</nav>
				</div>

				{/* User Info & Logout */}
				<div className="flex items-center space-x-3">
					{user && (
						<div className="text-right hidden sm:block">
							<div className="text-xs font-semibold text-slate-200">
								{user.first_name ? `${user.first_name} ${user.last_name || ""}` : user.email}
							</div>
							<div className="text-[10px] text-slate-400 flex items-center justify-end space-x-1">
								<span>{user.email}</span>
								<span>•</span>
								<span className="font-bold text-indigo-400 uppercase">{user.role}</span>
							</div>
						</div>
					)}

					<button
						onClick={handleLogout}
						className="px-3 py-1.5 bg-slate-800 hover:bg-red-500/20 hover:border-red-500/40 text-slate-300 hover:text-red-300 border border-slate-700 rounded-lg text-xs font-semibold transition"
					>
						Logout
					</button>
				</div>
			</header>

			{/* Main Content */}
			<main className="flex-1">{children}</main>
		</div>
	);
};

// Root App Component
export default function App() {
	return (
		<AuthProvider>
			<BrowserRouter>
				<AppRoutes />
			</BrowserRouter>
		</AuthProvider>
	);
}

const AppRoutes: React.FC = () => {
	const { user, isAuthenticated, isLoading } = useAuth();

	if (isLoading) {
		return (
			<div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
				<div className="flex items-center space-x-3">
					<svg className="animate-spin h-6 w-6 text-indigo-500" fill="none" viewBox="0 0 24 24">
						<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
						<path
							className="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					<span className="text-sm font-medium text-slate-300">Loading HR Platform...</span>
				</div>
			</div>
		);
	}

	return (
		<Routes>
			{/* Public Login Route */}
			<Route path="/login" element={isAuthenticated ? <Navigate to={user?.role === "HR_ADMIN" ? "/dashboard" : "/chat"} replace /> : <LoginPage />} />

			{/* Chatbot Route */}
			<Route
				path="/chat"
				element={
					<ProtectedRoute>
						<MainLayout>
							<ChatbotPage />
						</MainLayout>
					</ProtectedRoute>
				}
			/>

			{/* HR Admin Dashboard Route */}
			<Route
				path="/dashboard"
				element={
					<ProtectedRoute allowedRoles={["HR_ADMIN"]}>
						<MainLayout>
							<DashboardPage />
						</MainLayout>
					</ProtectedRoute>
				}
			/>

			{/* Default Route */}
			<Route
				path="/"
				element={isAuthenticated ? <Navigate to={user?.role === "HR_ADMIN" ? "/dashboard" : "/chat"} replace /> : <Navigate to="/login" replace />}
			/>

			{/* Catch-all Route */}
			<Route path="*" element={<Navigate to="/" replace />} />
		</Routes>
	);
};
