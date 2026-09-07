export type UserRole = "EMPLOYEE" | "HR_ADMIN";

export interface UserPayload {
	user_id: string;
	employee_id?: string | null;
	employee_number?: string | null;
	email: string;
	role: UserRole;
	first_name?: string | null;
	last_name?: string | null;
}

export interface LoginResponse {
	access_token: string;
	token_type: string;
	user_id: string;
	employee_id?: string | null;
	employee_number?: string | null;
	email: string;
	role: UserRole;
	first_name?: string | null;
	last_name?: string | null;
}

export interface APIResponseModel<T> {
	status_code: number;
	is_success: boolean;
	message: string;
	payload: T | null;
	error?: string | null;
}
