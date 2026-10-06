const { createCheckoutController } = require('./checkoutController');
const { createAdminController } = require('./adminController');
const { createUserController } = require('./userController');

function createControllers({ models, services }) {
    return {
        checkout: createCheckoutController({ checkoutService: services.checkout }),
        admin: createAdminController({ financialReportService: services.financialReport }),
        user: createUserController({ models }),
    };
}

module.exports = { createControllers };
