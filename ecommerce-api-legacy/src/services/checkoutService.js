const { hashPassword, randomPassword } = require('../utils/password');
const { NotFoundError, PaymentDeclinedError } = require('../utils/errors');
const { isPaid } = require('../models/paymentModel');
const logger = require('../utils/logger');

function createCheckoutService({ db, models, paymentGateway }) {
    const { users, courses, enrollments, payments, auditLogs } = models;
    const newPasswordHash = (password) => hashPassword(password || randomPassword());

    async function checkout({ name, email, password, courseId, cardNumber }) {
        const course = courseId === null ? null : await courses.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        // Leitura prévia só para calcular o hash fora da transação (scrypt é lento).
        const knownUser = await users.findByEmail(email);

        // Cobrança antes da primeira escrita: pagamento recusado não grava nada.
        const status = paymentGateway.charge(cardNumber, course.price);
        if (!isPaid(status)) throw new PaymentDeclinedError();

        const passwordHash = knownUser ? null : await newPasswordHash(password);

        // A busca decisiva acontece dentro da transação: checkouts simultâneos com
        // o mesmo e-mail novo não criam usuários duplicados.
        const enrollment = await db.transaction(async () => {
            const user = await users.findByEmail(email) || await users.create({
                name, email, passwordHash: passwordHash ?? await newPasswordHash(password),
            });
            const created = await enrollments.create(user.id, course.id);
            await payments.create(created.id, course.price, status);
            await auditLogs.record(`Checkout curso ${course.id} por ${user.id}`);
            return created;
        });

        logger.info(`Checkout concluído: matrícula ${enrollment.id} (curso ${course.id}, usuário ${enrollment.userId})`);
        return { enrollmentId: enrollment.id };
    }

    return { checkout };
}

module.exports = { createCheckoutService };
