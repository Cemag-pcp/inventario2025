from flask import render_template, jsonify, send_file, request
import pandas as pd
from . import db
import io
from app.models import Local, Peca, Quantidade
from sqlalchemy import text
from flask import current_app as app


@app.route("/", methods=["GET"])
def index():
    locais = db.session.query(Local.nome, Local.almoxarifado).distinct().all()
    return render_template("local/local_list.html", locais=locais)


@app.route("/inventario/<local_nome>/<almoxarifado>", methods=["GET"])
def local(local_nome, almoxarifado):
    # Filtrando estantes do local especificado
    query_estantes = text(
        """
        SELECT DISTINCT estante
        FROM inventario_2025.locais
        WHERE nome = :local_nome
        ORDER BY estante
        """
    )
    result_estantes = db.session.execute(query_estantes, {"local_nome": local_nome})
    estantes = [row[0] for row in result_estantes.fetchall()]

    # Consultando as peças diretamente com SQL
    query_pecas = text(
        """
        SELECT peca.id,
               peca.codigo,
               peca.descricao,
               peca.local_id,
               local.estante
        FROM inventario_2025.pecas AS peca
        JOIN inventario_2025.locais AS local ON peca.local_id = local.id
        LEFT JOIN inventario_2025.quantidades AS quant ON peca.id = quant.peca_id
        WHERE local.nome = :local_nome
          AND almoxarifado = :almoxarifado
          AND quant.id IS NULL
          AND peca.peca_fora_lista = FALSE
        ORDER BY estante
        """
    )

    result_pecas = db.session.execute(
        query_pecas, {"local_nome": local_nome, "almoxarifado": almoxarifado}
    )
    pecas = result_pecas.fetchall()

    pecas_dict = [
        {
            "id": peca.id,
            "codigo": peca.codigo,
            "descricao": peca.descricao,
            "local_id": peca.local_id,
            "local_estante": peca.estante,
        }
        for peca in pecas
    ]

    return render_template(
        "local/dados_inventario.html", pecas=pecas_dict, estantes=estantes, local=local_nome
    )


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard/dashboard.html")


@app.route("/api/fora-da-lista", methods=["POST"])
def fora_da_lista():
    data = request.get_json()

    local_nome = data.get("localNome")
    codigo_peca = data.get("codigoPecaForaLista")
    descricao_peca = data.get("descricaoPecaForaLista")
    estante = data.get("estantePecaForaLista")
    quantidade = data.get("quantidadePecaForaLista")
    peca_fora_lista = True

    if not all([local_nome, codigo_peca, quantidade]):
        return jsonify({"message": "Preencha todos os campos obrigatórios"}), 400

    local = Local.query.filter_by(nome=local_nome, estante=estante).first()
    if not local:
        return jsonify({"message": "Local não encontrado"}), 404

    peca_existente = Peca.query.filter_by(codigo=codigo_peca, local_id=local.id).first()
    if peca_existente:
        return jsonify({"message": "Peça já existe no local"}), 400

    nova_peca = Peca(
        codigo=codigo_peca,
        descricao=descricao_peca,
        local_id=local.id,
        quantidade_sistema=0,
        peca_fora_lista=peca_fora_lista,
    )
    db.session.add(nova_peca)
    db.session.commit()

    nova_quantidade = Quantidade(quantidade=quantidade, peca_id=nova_peca.id)
    db.session.add(nova_quantidade)
    db.session.commit()

    return jsonify({"message": "Peça fora da lista adicionada com sucesso"}), 201


@app.route("/api/inventario", methods=["POST"])
def quantidadePecas():
    data = request.get_json()
    id_local = data.get("id")
    codigo_peca = data.get("peca")
    quantidade = data.get("quantidade")

    if not all([id_local, codigo_peca, quantidade]):
        return jsonify(
            {"message": "Todos os campos são obrigatórios e devem ser preenchidos"}
        ), 400

    try:
        quantidade = float(quantidade)
    except ValueError:
        return jsonify({"message": "Quantidade deve ser um número válido"}), 400

    if quantidade < 0:
        return jsonify({"message": "Quantidade não pode ser menor que 0"}), 400

    local = Local.query.filter_by(id=id_local).first()
    if not local:
        return jsonify({"message": "Local não encontrado"}), 400

    peca_obj = Peca.query.filter_by(local_id=id_local, codigo=codigo_peca).first()
    if not peca_obj:
        return jsonify({"message": "Peça não encontrada no local especificado"}), 401

    quantidade_existente = (
        Quantidade.query.join(Peca)
        .join(Local)
        .filter(
            Peca.id == peca_obj.id,
            Local.id == id_local,
            Peca.local_id == id_local,
            Peca.codigo == codigo_peca,
        )
        .first()
    )

    if quantidade_existente:
        return jsonify(
            {"message": "Já existe uma quantidade registrada para esta peça e estante"}
        ), 402

    nova_quantidade = Quantidade(quantidade=quantidade, peca_id=peca_obj.id)
    db.session.add(nova_quantidade)
    db.session.commit()

    return jsonify({"message": "Quantidade registrada com sucesso"}), 200


@app.route("/api/dashboard", methods=["GET"])
def pecas_contagem():
    almoxarifados_data = []

    almoxarifados = db.session.query(Local.almoxarifado).distinct().all()

    for almoxarifado in almoxarifados:
        almoxarifado_name = almoxarifado[0]

        contadas = (
            db.session.query(Peca)
            .join(Local)
            .join(Quantidade, isouter=True)
            .filter(Local.almoxarifado == almoxarifado_name, Quantidade.id != None)
            .count()
        )

        nao_contadas = (
            db.session.query(Peca)
            .join(Local)
            .join(Quantidade, isouter=True)
            .filter(Local.almoxarifado == almoxarifado_name, Quantidade.id == None)
            .count()
        )

        total = contadas + nao_contadas
        contadas_percent = (contadas / total) * 100 if total > 0 else 0
        nao_contadas_percent = (nao_contadas / total) * 100 if total > 0 else 0

        almoxarifados_data.append(
            {
                "almoxarifado": almoxarifado_name,
                "contadas": round(contadas_percent, 2),
                "nao_contadas": round(nao_contadas_percent, 2),
            }
        )

    return jsonify(almoxarifados_data)


@app.route("/api/comparar-quantidade", methods=["GET"])
def comparar_quantidade():
    resultados = (
        db.session.query(
            Local.almoxarifado,
            Peca.id.label("peca_id"),
            Local.nome.label("local_nome"),
            Peca.codigo,
            Peca.descricao,
            Peca.peca_fora_lista,
            Peca.quantidade_sistema,
            Quantidade.quantidade.label("quantidade_real"),
        )
        .join(Peca, Local.id == Peca.local_id)
        .outerjoin(Quantidade, Peca.id == Quantidade.peca_id)
        .all()
    )

    comparacoes = []
    for resultado in resultados:
        comparacoes.append(
            {
                "almoxarifado": resultado.almoxarifado,
                "peca_id": resultado.peca_id,
                "local": resultado.local_nome,
                "codigo": resultado.codigo,
                "descricao": resultado.descricao,
                "peca_fora_lista": resultado.peca_fora_lista,
                "quantidade_sistema": resultado.quantidade_sistema,
                "quantidade_real": resultado.quantidade_real,
                "diferenca": (
                    resultado.quantidade_real - resultado.quantidade_sistema
                    if resultado.quantidade_sistema is not None
                    and resultado.quantidade_real is not None
                    else None
                ),
            }
        )

    if request.args.get("export") == "excel":
        df = pd.DataFrame(comparacoes)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Comparacoes")
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="comparacoes.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    return jsonify(comparacoes)


@app.route("/api/quantidade-real", methods=["POST"])
def atualizar_quantidade_real():
    data = request.get_json()

    peca_id = data.get("peca_id")
    quantidade_real = data.get("quantidade_real")

    if peca_id is None or quantidade_real is None:
        return jsonify({"message": "Peça e quantidade são obrigatórias"}), 400

    try:
        quantidade_real = float(quantidade_real)
    except (TypeError, ValueError):
        return jsonify({"message": "Quantidade deve ser um número válido"}), 400

    if quantidade_real < 0:
        return jsonify({"message": "Quantidade não pode ser menor que 0"}), 400

    peca = Peca.query.get(peca_id)
    if not peca:
        return jsonify({"message": "Peça não encontrada"}), 404

    quantidade_obj = Quantidade.query.filter_by(peca_id=peca.id).first()

    if quantidade_obj:
        quantidade_obj.quantidade = quantidade_real
    else:
        quantidade_obj = Quantidade(quantidade=quantidade_real, peca_id=peca.id)
        db.session.add(quantidade_obj)

    db.session.commit()

    return jsonify({"message": "Quantidade real atualizada com sucesso"}), 200

