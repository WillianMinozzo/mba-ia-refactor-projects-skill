const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../models/paymentModel');

// Popula apenas um banco vazio (com :memory:, a cada boot, como antes).
async function seedIfEmpty(db) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM users');
    if (total > 0) return;

    await db.transaction(async () => {
        await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', await hashPassword('123')]);
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
            ['Clean Architecture', 997.0, 'Docker', 497.0]);
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)',
            [PAYMENT_STATUS.PAID]);
    });
}

module.exports = { seedIfEmpty };
