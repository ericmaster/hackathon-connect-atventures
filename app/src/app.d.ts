// See https://svelte.dev/docs/kit/types#app.d.ts
declare global {
	namespace App {}
	interface ImportMetaEnv {
		readonly VITE_FV_API_URL?: string;
		readonly VITE_FV_IDENTITY_POOL_ID?: string;
		readonly VITE_FV_REGION?: string;
		readonly VITE_FV_TRANSPORT?: 'fake' | 'http';
	}
}

export {};
