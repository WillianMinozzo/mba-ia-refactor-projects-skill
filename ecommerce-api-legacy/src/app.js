const express = require('express');
const config = require('./config');
const logger = require('./utils/logger');
const { createConnection } = require('./database/connection');
const { createSchema } = require('./database/schema');
const { seedIfEmpty } = require('./database/seed');
const { createModels } = require('./models');
const { createServices } = require('./services');
const { createControllers } = require('./controllers');
const { createRoutes } = require('./routes');
const { requireAdmin } = require('./middlewares/adminAuth');
const { errorHandler } = require('./middlewares/errorHandler');

// Composition root: monta config → dados → models → services → controllers → rotas.
function createApp({ db }) {
    const models = createModels(db);
    const services = createServices({ db, models, config });
    const controllers = createControllers({ models, services });

    const app = express();
    app.use(express.json());
    app.use('/api', createRoutes({ controllers, adminGuard: requireAdmin(config) }));
    app.use(errorHandler);
    return app;
}

async function start() {
    for (const name of config.ephemeralSecrets) logger.warn(`${name} não definida; usando valor efêmero`);
    if (!config.adminToken) {
        logger.warn(config.env === 'production'
            ? 'ADMIN_TOKEN não definida; rotas administrativas desabilitadas (403)'
            : 'ADMIN_TOKEN não definida; rotas administrativas abertas sem X-Admin-Token');
    }

    const db = createConnection(config.dbFile);
    await createSchema(db);
    await seedIfEmpty(db);

    createApp({ db }).listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        logger.error('Falha ao iniciar a aplicação', err);
        process.exit(1);
    });
}

module.exports = { createApp, start };
