const { parseUserId } = require('../validators/userValidator');
const logger = require('../utils/logger');

// Texto contratual mantido sem alteração, embora matrículas e pagamentos agora
// sejam removidos junto com o usuário.
const USER_DELETED_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

function createUserController({ models }) {
    return {
        async remove(req, res) {
            const id = parseUserId(req.params.id);
            const removed = id !== null && await models.users.remove(id);
            logger.info(`DELETE usuário ${req.params.id}: ${removed ? 'removido' : 'inexistente'}`);
            res.send(USER_DELETED_MESSAGE);
        },
    };
}

module.exports = { createUserController };
