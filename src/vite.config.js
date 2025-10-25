import { defineConfig } from 'vite';

// Use dynamic import for plugins to avoid "require() of ES Module" errors
// when a CommonJS loader attempts to require an ESM package in CI.
export default defineConfig(async () => {
    const { default: react } = await import('@vitejs/plugin-react');
    return {
        plugins: [react()],
        build: {
            outDir: 'dist', // Changed from 'build' to 'dist' to match Dockerfile
        },
        esbuild: {
            charset: 'utf8',
            loader: 'jsx',
            jsxFactory: 'React.createElement',
            jsxFragment: 'React.Fragment',
        },
    };
});
