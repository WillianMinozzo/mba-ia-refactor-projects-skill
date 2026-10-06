const { toPositiveInteger } = require('./common');

// :id que não é inteiro positivo não corresponde a nenhum usuário (null).
// O contrato original responde a esse caso como a qualquer outra exclusão.
function parseUserId(value) {
    return toPositiveInteger(value);
}

module.exports = { parseUserId };
