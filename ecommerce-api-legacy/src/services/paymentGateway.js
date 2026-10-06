const logger = require('../utils/logger');
const { PAYMENT_STATUS } = require('../models/paymentModel');

// Gateway simulado: aprova cartões cujo número começa com este prefixo.
const APPROVED_CARD_PREFIX = '4';

const maskCard = (cardNumber) => `****${cardNumber.slice(-4)}`;

// A chave (config.paymentGatewayKey) é injetada para a integração com o
// provedor real e nunca deve aparecer em log.
function createPaymentGateway({ apiKey }) {
    if (!apiKey) throw new Error('Payment gateway key is required');
    return {
        charge(cardNumber, amount) {
            const status = cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
            logger.info(`Cobrança de ${amount} no cartão ${maskCard(cardNumber)}: ${status}`);
            return status;
        },
    };
}

module.exports = { createPaymentGateway };
