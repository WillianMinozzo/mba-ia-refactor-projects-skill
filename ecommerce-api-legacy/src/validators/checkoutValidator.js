const { ValidationError } = require('../utils/errors');
const { toPositiveInteger } = require('./common');

const isText = (value) => typeof value === 'string' || typeof value === 'number';

// Converte o corpo do checkout (chaves do contrato: usr, eml, pwd, c_id, card)
// em um comando. Responde 400 "Bad Request" nos mesmos casos do contrato
// original (campo obrigatório ausente) e onde o original derrubava o processo
// (card ou pwd que não são texto). c_id não numérico segue para o 404.
function validateCheckout(body) {
    const { usr, eml, pwd, c_id: rawCourseId, card } = body || {};

    if (!usr || !eml || !rawCourseId || !card) throw new ValidationError();
    if (!isText(usr) || !isText(eml) || typeof card !== 'string') throw new ValidationError();
    if (pwd && typeof pwd !== 'string') throw new ValidationError();

    return {
        name: String(usr),
        email: String(eml),
        password: pwd || null,
        courseId: toPositiveInteger(rawCourseId),
        cardNumber: card,
    };
}

module.exports = { validateCheckout };
