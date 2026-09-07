import path from "path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
	// Load env from workspace root (2 levels up from src/frontend) as well as process.cwd()
	const rootEnv = loadEnv(mode, path.resolve(process.cwd(), "../.."), "");
	const localEnv = loadEnv(mode, process.cwd(), "");
	const env = { ...rootEnv, ...localEnv };

	const backendBaseUrl = env.BACKEND_BASE_URL || "http://localhost:9000";

	return {
		plugins: [react(), tailwindcss()],
		define: {
			"import.meta.env.BACKEND_BASE_URL": JSON.stringify(backendBaseUrl),
			"import.meta.env.VITE_BACKEND_BASE_URL": JSON.stringify(backendBaseUrl),
		},
		server: {
			proxy: {
				"/api": {
					target: backendBaseUrl,
					changeOrigin: true,
				},
			},
		},
	};
});
