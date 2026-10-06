const { AsyncLocalStorage } = require('async_hooks');
const sqlite3 = require('sqlite3');

// Adaptador de Promises sobre o driver de callbacks do sqlite3.
//
// A conexão é única: um BEGIN aberto vale para qualquer comando enviado a ela.
// Por isso toda operação passa por uma fila; só os comandos emitidos de dentro
// da transação ativa (identificada por AsyncLocalStorage) furam a fila.
function createConnection(file) {
    const raw = new sqlite3.Database(file);
    const transactionScope = new AsyncLocalStorage();
    let queue = Promise.resolve();

    function enqueue(operation) {
        if (transactionScope.getStore()) return operation();
        const result = queue.then(operation);
        queue = result.catch(() => {});
        return result;
    }

    const rawRun = (sql, params = []) => new Promise((resolve, reject) =>
        raw.run(sql, params, function (err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        }));

    const run = (sql, params) => enqueue(() => rawRun(sql, params));

    const get = (sql, params = []) => enqueue(() => new Promise((resolve, reject) =>
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)))));

    const all = (sql, params = []) => enqueue(() => new Promise((resolve, reject) =>
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)))));

    // Tudo ou nada. Chamada de dentro de outra transação, participa dela.
    function transaction(work) {
        if (transactionScope.getStore()) return work();
        return enqueue(() => transactionScope.run(true, async () => {
            await rawRun('BEGIN');
            try {
                const value = await work();
                await rawRun('COMMIT');
                return value;
            } catch (err) {
                await rawRun('ROLLBACK');
                throw err;
            }
        }));
    }

    return { run, get, all, transaction };
}

module.exports = { createConnection };
