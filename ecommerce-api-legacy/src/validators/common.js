// Aceita número ou string numérica (o banco já comparava "2" com 2).
function toPositiveInteger(value) {
    const number = typeof value === 'string' && value.trim() !== '' ? Number(value) : value;
    return Number.isInteger(number) && number > 0 ? number : null;
}

module.exports = { toPositiveInteger };
