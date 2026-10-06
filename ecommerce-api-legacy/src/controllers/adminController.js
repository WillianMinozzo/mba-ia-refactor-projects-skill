function createAdminController({ financialReportService }) {
    return {
        async financialReport(req, res) {
            res.json(await financialReportService.build());
        },
    };
}

module.exports = { createAdminController };
