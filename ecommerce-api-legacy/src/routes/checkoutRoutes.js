const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function createCheckoutRoutes({ checkoutController }) {
    const router = express.Router();
    router.post('/checkout', asyncHandler(checkoutController.create));
    return router;
}

module.exports = { createCheckoutRoutes };
