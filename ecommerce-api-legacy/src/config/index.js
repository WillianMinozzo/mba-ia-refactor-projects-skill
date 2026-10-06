const crypto = require('crypto');

const env = process.env;
const EPHEMERAL_SECRET_BYTES = 32;
const ephemeralSecrets = [];

function secret(name) {
    if (env[name]) return env[name];
    if (env.NODE_ENV === 'production') throw new Error(`${name} must be set in production`);
    ephemeralSecrets.push(name);
    return crypto.randomBytes(EPHEMERAL_SECRET_BYTES).toString('hex');
}

module.exports = Object.freeze({
    env: env.NODE_ENV || 'development',
    port: Number(env.PORT) || 3000,
    dbFile: env.DB_FILE || ':memory:',
    logLevel: env.LOG_LEVEL || 'info',
    paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
    // Opcional: quando definido, as rotas administrativas exigem X-Admin-Token.
    adminToken: env.ADMIN_TOKEN || '',
    ephemeralSecrets: Object.freeze(ephemeralSecrets),
});
