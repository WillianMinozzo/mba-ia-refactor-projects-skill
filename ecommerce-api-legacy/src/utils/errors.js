// Erros de domínio com o status HTTP correspondente. A mensagem é o corpo
// de texto que a API já devolvia para cada caso.
class AppError extends Error {
    constructor(status, message) {
        super(message);
        this.name = this.constructor.name;
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') { super(400, message); }
}

class NotFoundError extends AppError {
    constructor(message) { super(404, message); }
}

class PaymentDeclinedError extends AppError {
    constructor(message = 'Pagamento recusado') { super(400, message); }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentDeclinedError };
