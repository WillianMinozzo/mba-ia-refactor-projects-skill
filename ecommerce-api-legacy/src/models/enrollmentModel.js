function createEnrollmentModel(db) {
    return {
        async create(userId, courseId) {
            const { lastID } = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId]);
            return { id: lastID, userId, courseId };
        },
    };
}

module.exports = { createEnrollmentModel };
