const crypto = require('crypto');

const ADMIN_TOKEN_HEADER = 'x-admin-token';

// Guarda das rotas administrativas (relatório financeiro, exclusão de usuário).
// - ADMIN_TOKEN definido: exige X-Admin-Token igual (401 sem ele).
// - Sem ADMIN_TOKEN: fora de produção a rota responde como sempre respondeu;
//   em produção fica desabilitada (403).
function requireAdmin({ adminToken, env }) {
    const expected = Buffer.from(adminToken || '');
    return (req, res, next) => {
        if (expected.length === 0) {
            return env === 'production' ? res.status(403).send('Rota administrativa desabilitada') : next();
        }
        const provided = Buffer.from(String(req.get(ADMIN_TOKEN_HEADER) || ''));
        const ok = provided.length === expected.length && crypto.timingSafeEqual(provided, expected);
        return ok ? next() : res.status(401).send('Não autorizado');
    };
}

module.exports = { requireAdmin };
