const { logLevel } = require('../config');

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };
const threshold = LEVELS[logLevel] || LEVELS.info;

function write(level, message) {
    if (LEVELS[level] < threshold) return;
    const line = `${new Date().toISOString()} [${level.toUpperCase()}] ${message}`;
    (level === 'error' ? console.error : level === 'warn' ? console.warn : console.log)(line);
}

module.exports = {
    debug: (msg) => write('debug', msg),
    info: (msg) => write('info', msg),
    warn: (msg) => write('warn', msg),
    error: (msg, err) => write('error', err ? `${msg}: ${err.stack || err}` : msg),
};
