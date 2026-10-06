const { validateCheckout } = require('../validators/checkoutValidator');

function createCheckoutController({ checkoutService }) {
    return {
        async create(req, res) {
            const command = validateCheckout(req.body);
            const { enrollmentId } = await checkoutService.checkout(command);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
