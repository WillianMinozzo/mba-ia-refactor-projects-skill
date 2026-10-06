const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function createUserRoutes({ userController, adminGuard }) {
    const router = express.Router();
    router.delete('/users/:id', adminGuard, asyncHandler(userController.remove));
    return router;
}

module.exports = { createUserRoutes };
