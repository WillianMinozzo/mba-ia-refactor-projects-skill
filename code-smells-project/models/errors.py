class AppError(Exception):
    """Erro de domínio convertido em resposta pelo handler central.

    `com_sucesso` preserva o formato das rotas que já respondiam {"erro", "sucesso": false}.
    """

    status = 400

    def __init__(self, mensagem, com_sucesso=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.com_sucesso = com_sucesso


class ValidationError(AppError):
    status = 400


class BusinessRuleError(AppError):
    status = 400


class BancoIndisponivelError(AppError):
    status = 500
