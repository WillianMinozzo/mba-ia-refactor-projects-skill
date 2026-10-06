function createUserModel(db) {
    return {
        findByEmail(email) {
            return db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
        },

        // Recebe a senha já com hash: o model nunca vê a senha em texto puro.
        async create({ name, email, passwordHash }) {
            const { lastID } = await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, passwordHash]);
            return { id: lastID, name, email };
        },

        // Remove o usuário com suas matrículas e pagamentos (sem FK no schema).
        remove(id) {
            return db.transaction(async () => {
                await db.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
                await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
                const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
                return changes > 0;
            });
        },
    };
}

module.exports = { createUserModel };
