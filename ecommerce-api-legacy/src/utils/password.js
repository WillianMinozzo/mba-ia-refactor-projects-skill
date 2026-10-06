const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const RANDOM_PASSWORD_BYTES = 18;
const SCHEME = 'scrypt';

async function hashPassword(raw) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const key = await scrypt(raw, salt, KEY_LENGTH);
    return `${SCHEME}$${salt}$${key.toString('hex')}`;
}

// Usada quando o cliente não informa senha: nunca um valor fixo e conhecido.
function randomPassword() {
    return crypto.randomBytes(RANDOM_PASSWORD_BYTES).toString('base64url');
}

module.exports = { hashPassword, randomPassword };
