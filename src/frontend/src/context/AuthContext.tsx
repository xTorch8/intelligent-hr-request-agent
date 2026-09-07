import React, { createContext, useContext, useEffect, useState } from "react";
import type { UserPayload, UserRole } from "../types/auth";
import { getMeApi, loginApi } from "../services/api";

interface AuthContextType {
	user: UserPayload | null;
	token: string | null;
	isLoading: boolean;
	login: (email: string, pass: string) => Promise<UserPayload>;
	logout: () => void;
	isAuthenticated: boolean;
	role: UserRole | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const [user, setUser] = useState<UserPayload | null>(null);
	const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));
	const [isLoading, setIsLoading] = useState<boolean>(true);

	useEffect(() => {
		async function initAuth() {
			const storedToken = localStorage.getItem("token");
			if (storedToken) {
				try {
					const res = await getMeApi();
					if (res.is_success && res.payload) {
						setUser(res.payload);
					} else {
						// Invalid token
						localStorage.removeItem("token");
						setToken(null);
						setUser(null);
					}
				} catch {
					localStorage.removeItem("token");
					setToken(null);
					setUser(null);
				}
			} else {
				setUser(null);
			}
			setIsLoading(false);
		}
		initAuth();
	}, []);

	const login = async (email: string, pass: string): Promise<UserPayload> => {
		setIsLoading(true);
		try {
			const response = await loginApi(email, pass);
			if (!response.is_success || !response.payload) {
				throw new Error(response.message || response.error || "Login failed");
			}

			const payload = response.payload;
			const newToken = payload.access_token;
			localStorage.setItem("token", newToken);
			setToken(newToken);

			const userProfile: UserPayload = {
				user_id: payload.user_id,
				employee_id: payload.employee_id,
				employee_number: payload.employee_number,
				email: payload.email,
				role: payload.role,
				first_name: payload.first_name,
				last_name: payload.last_name,
			};

			setUser(userProfile);
			setIsLoading(false);
			return userProfile;
		} catch (err) {
			setIsLoading(false);
			throw err;
		}
	};

	const logout = () => {
		localStorage.removeItem("token");
		setToken(null);
		setUser(null);
	};

	return (
		<AuthContext.Provider
			value={{
				user,
				token,
				isLoading,
				login,
				logout,
				isAuthenticated: !!token && !!user,
				role: user?.role || null,
			}}
		>
			{children}
		</AuthContext.Provider>
	);
};

export const useAuth = () => {
	const context = useContext(AuthContext);
	if (!context) {
		throw new Error("useAuth must be used within an AuthProvider");
	}
	return context;
};
