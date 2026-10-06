const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

const INTERNAL_ERROR_MESSAGE = 'Erro interno do servidor';

// Express 4 não propaga rejeições de handlers async: encaminha para next().
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// Corpo em texto puro, no mesmo formato que a API sempre usou para erros.
function errorHandler(err, req, res, next) {
    if (res.headersSent) return next(err);
    if (err instanceof AppError) return res.status(err.status).send(err.message);
    if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');
    logger.error(`${req.method} ${req.originalUrl} falhou`, err);
    return res.status(500).send(INTERNAL_ERROR_MESSAGE);
}

module.exports = { asyncHandler, errorHandler };
