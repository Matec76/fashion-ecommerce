// Production-safe logging utility
// Automatically disables logs in production mode

const isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';

const logger = {
    log: (...args) => {
        if (isDevelopment) {
            console.log(...args);
        }
    },
    error: (...args) => {
        // Always log errors, even in production
        console.error(...args);
    },
    warn: (...args) => {
        if (isDevelopment) {
            console.warn(...args);
        }
    },
    debug: (...args) => {
        if (isDevelopment) {
            console.log('[DEBUG]', ...args);
        }
    }
};

export default logger;
