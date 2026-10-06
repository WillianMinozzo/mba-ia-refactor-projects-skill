const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

const isPaid = (status) => status === PAYMENT_STATUS.PAID;

function createPaymentModel(db) {
    return {
        async create(enrollmentId, amount, status) {
            const { lastID } = await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status]);
            return { id: lastID, enrollmentId, amount, status };
        },
    };
}

module.exports = { createPaymentModel, PAYMENT_STATUS, isPaid };
