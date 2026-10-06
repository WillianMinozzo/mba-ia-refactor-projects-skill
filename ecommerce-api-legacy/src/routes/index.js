const express = require('express');
const { createCheckoutRoutes } = require('./checkoutRoutes');
const { createAdminRoutes } = require('./adminRoutes');
const { createUserRoutes } = require('./userRoutes');

// Monta todas as rotas sob /api (caminhos idênticos aos originais).
function createRoutes({ controllers, adminGuard }) {
    const router = express.Router();
    router.use(createCheckoutRoutes({ checkoutController: controllers.checkout }));
    router.use(createAdminRoutes({ adminController: controllers.admin, adminGuard }));
    router.use(createUserRoutes({ userController: controllers.user, adminGuard }));
    return router;
}

module.exports = { createRoutes };
