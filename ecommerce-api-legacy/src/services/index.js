const { createPaymentGateway } = require('./paymentGateway');
const { createCheckoutService } = require('./checkoutService');
const { createFinancialReportService } = require('./financialReportService');

function createServices({ db, models, config }) {
    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey });
    return {
        checkout: createCheckoutService({ db, models, paymentGateway }),
        financialReport: createFinancialReportService({ models }),
    };
}

module.exports = { createServices };
