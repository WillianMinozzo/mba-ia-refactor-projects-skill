from models.errors import ValidationError
from models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_TAMANHO_MAX, NOME_TAMANHO_MIN

CAMPOS_OBRIGATORIOS = (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque"))


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar_produto(dados, regras_de_criacao=True):
    """Valida o corpo de criação/atualização de produto.

    A atualização nunca validou tamanho do nome nem categoria; essas regras ficam
    restritas à criação para não alterar o contrato do PUT.
    """
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    for campo, rotulo in CAMPOS_OBRIGATORIOS:
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not _numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not _numero(estoque):
        raise ValidationError("Estoque deve ser numérico")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")

    if regras_de_criacao:
        if len(nome) < NOME_TAMANHO_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_TAMANHO_MAX:
            raise ValidationError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not isinstance(categoria, str):
        raise ValidationError("Categoria inválida")

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtros_busca(args):
    filtros = {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria", None),
        "preco_min": args.get("preco_min", None),
        "preco_max": args.get("preco_max", None),
    }
    try:
        for chave in ("preco_min", "preco_max"):
            if filtros[chave]:
                filtros[chave] = float(filtros[chave])
    except ValueError:
        raise ValidationError("Filtro de preço inválido") from None
    return filtros
