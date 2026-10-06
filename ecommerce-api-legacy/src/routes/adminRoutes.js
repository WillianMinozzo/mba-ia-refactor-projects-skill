const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function createAdminRoutes({ adminController, adminGuard }) {
    const router = express.Router();
    router.get('/admin/financial-report', adminGuard, asyncHandler(adminController.financialReport));
    return router;
}

module.exports = { createAdminRoutes };
