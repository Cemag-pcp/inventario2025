from flask import render_template, jsonify, send_file, request
import pandas as pd
from . import db
import io
from app.models import Local,Peca, Quantidade
from sqlalchemy import text  # Importar a função 'text' para executar SQL puro
from flask import current_app as app

@app.route("/", methods=['GET'])
def index():
    locais = db.session.query(Local.nome, Local.almoxarifado).distinct().all()
    return render_template("local/local_list.html", locais=locais)

@app.route("/inventario/<local_nome>/<almoxarifado>", methods=['GET'])
def local(local_nome,almoxarifado):
    # Filtrando estante no local especificado
    query_estantes = text('''
        SELECT DISTINCT estante
        FROM inventario_2025.locais
        WHERE nome = :local_nome
        ORDER by estante             
    ''')
    result_estantes = db.session.execute(query_estantes, {'local_nome': local_nome})
    estantes = [row[0] for row in result_estantes.fetchall()]

    # Consultando as peças diretamente com SQL puro
    query_pecas = text('''
        SELECT peca.id, peca.codigo, peca.descricao, peca.local_id, local.estante
        FROM inventario_2025.pecas AS peca
        JOIN inventario_2025.locais AS local ON peca.local_id = local.id
        LEFT JOIN inventario_2025.quantidades AS quant ON peca.id = quant.peca_id
        WHERE local.nome = :local_nome and almoxarifado = :almoxarifado
        AND quant.id IS NULL
        AND peca.peca_fora_lista = FALSE
        ORDER by estante 
    ''')
    
    result_pecas = db.session.execute(query_pecas, {'local_nome': local_nome,'almoxarifado':almoxarifado})
    pecas = result_pecas.fetchall()

    # Convertendo os resultados para um formato de dicionário
    pecas_dict = [
        {
            "id": peca.id,
            "codigo": peca.codigo,
            "descricao": peca.descricao,
            "local_id": peca.local_id,
            "local_estante": peca.estante
        }
        for peca in pecas
    ]
    
    # Retornando os dados ao template
    return render_template("local/dados_inventario.html", pecas=pecas_dict, estantes=estantes, local=local_nome)

@app.route("/dashboard", methods=['GET'])
def dashboard():
    return render_template("dashboard/dashboard.html")

@app.route("/api/fora-da-lista", methods=['POST'])
def fora_da_lista():
    data = request.get_json()

    localNome = data.get('localNome')
    codigoPecaForaLista = data.get('codigoPecaForaLista')
    descricaoPecaForaLista = data.get('descricaoPecaForaLista')
    estantePecaForaLista = data.get('estantePecaForaLista')
    quantidadePecaForaLista = data.get('quantidadePecaForaLista')
    peca_fora_lista = True

    # Verificação dos campos obrigatórios
    if not all([localNome, codigoPecaForaLista, quantidadePecaForaLista]):
        print("Preencha todos os campos obrigatórios")
        print(data)
        return jsonify({'message': 'Preencha todos os campos obrigatórios'}), 400

    # Verifique se o Local com o nome e estante especificados existe
    local = Local.query.filter_by(nome=localNome, estante=estantePecaForaLista).first()
    if not local:
        print("Local não encontrado")
        return jsonify({'message': 'Local não encontrado'}), 404

    # Verifique se já existe uma Peça com o mesmo código no Local
    peca_existente = Peca.query.filter_by(codigo=codigoPecaForaLista, local_id=local.id).first()
    if peca_existente:
        print("Peça já existe no local")
        return jsonify({'message': 'Peça já existe no local'}), 400

    # Criar a nova peça e quantidade
    nova_peca = Peca(
        codigo=codigoPecaForaLista,
        descricao=descricaoPecaForaLista,
        local_id=local.id,
        quantidade_sistema=0,
        peca_fora_lista=peca_fora_lista
    )
    db.session.add(nova_peca)
    db.session.commit()

    # Criar a nova quantidade associada à peça
    nova_quantidade = Quantidade(
        quantidade=quantidadePecaForaLista,
        peca_id=nova_peca.id
    )
    db.session.add(nova_quantidade)
    db.session.commit()

    return jsonify({'message': 'Peça fora da lista adicionada com sucesso'}), 201

@app.route("/api/inventario", methods=['POST'])
def quantidadePecas():
    data = request.get_json()
    idLocal = data.get('id')
    peca = data.get('peca')
    quantidade = data.get('quantidade')
    
    if not all([idLocal, peca, quantidade]):
        print("Algum campo vazio")
        return jsonify({'message': 'Todos os campos são obrigatórios e devem ser preenchidos'}), 400
    
    try:
        quantidade = float(quantidade)  # Converter quantidade para float
    except ValueError:
        return jsonify({'message': 'Quantidade deve ser um número válido'}), 400
    
    if quantidade < 0:
        return jsonify({'message': 'Quantidade não pode ser menor que 0'}), 400

    # Verificando se já existe uma quantidade associada à peça, local e estante fornecidos
    local = Local.query.filter_by(id=idLocal).first()
    if not local:
        print("Local não encontrado")
        return jsonify({'message': 'Local não encontrado'}), 400

    # Verificando se a peça e estante pertencem ao local
    peca_obj = Peca.query.filter_by(local_id=idLocal, codigo=peca).first()
    if not peca_obj:
        print("Peça não encontrada no local especificado")
        return jsonify({'message': 'Peça não encontrada no local especificado'}), 401

    # Verificar se já existe uma quantidade registrada para a peça e estante
    quantidade_existente = Quantidade.query.join(Peca).join(Local).filter(
        Peca.id == peca_obj.id,
        Local.id == idLocal,
        Peca.local_id == idLocal,
        Peca.codigo == peca,
    ).first()

    if quantidade_existente:
        print("Já existe uma quantidade registrada para esta peça e estante")
        return jsonify({'message': 'Já existe uma quantidade registrada para esta peça e estante'}), 402

    # Se não houver quantidade registrada, adiciona a nova quantidade
    nova_quantidade = Quantidade(
        quantidade=quantidade,
        peca_id=peca_obj.id
    )
    db.session.add(nova_quantidade)
    db.session.commit()

    return jsonify({'message': 'Quantidade registrada com sucesso'}), 200

@app.route("/api/dashboard", methods=['GET'])
def pecas_contagem():
    almoxarifados_data = []

    # Obtém todos os almoxarifados distintos
    almoxarifados = db.session.query(Local.almoxarifado).distinct().all()

    # Itera sobre cada almoxarifado e agrupa as peças
    for almoxarifado in almoxarifados:
        almoxarifado_name = almoxarifado[0]
        
        # Conta as peças contadas (com quantidade) por almoxarifado
        contadas = db.session.query(Peca).join(Local).join(Quantidade, isouter=True).filter(
            Local.almoxarifado == almoxarifado_name,
            Quantidade.id != None  # Garante que a peça tem uma quantidade associada
        ).count()
        
        # Conta as peças não contadas (sem quantidade) por almoxarifado
        nao_contadas = db.session.query(Peca).join(Local).join(Quantidade, isouter=True).filter(
            Local.almoxarifado == almoxarifado_name,
            Quantidade.id == None  # Garante que a peça não tem uma quantidade associada
        ).count()

        # Calcula a porcentagem de contadas e não contadas
        total = contadas + nao_contadas
        contadas_percent = (contadas / total) * 100 if total > 0 else 0
        nao_contadas_percent = (nao_contadas / total) * 100 if total > 0 else 0

        # Adiciona os dados ao dicionário
        almoxarifados_data.append({
            'almoxarifado': almoxarifado_name,
            'contadas': round(contadas_percent,2),
            'nao_contadas': round(nao_contadas_percent,2)
        })

    return jsonify(almoxarifados_data)

@app.route("/api/comparar-quantidade", methods=['GET'])
def comparar_quantidade():
    # Consulta para buscar as peças com suas respectivas informações
    resultados = db.session.query(
        Local.almoxarifado,
        Local.nome.label('local_nome'),
        Peca.codigo,
        Peca.descricao,
        Peca.peca_fora_lista,
        Peca.quantidade_sistema,
        Quantidade.quantidade.label('quantidade_real')
    ).join(Peca, Local.id == Peca.local_id) \
     .outerjoin(Quantidade, Peca.id == Quantidade.peca_id) \
     .all()

    # Formata os dados em uma lista de dicionários para fácil manipulação
    comparacoes = []
    for resultado in resultados:
        comparacoes.append({
            'almoxarifado': resultado.almoxarifado,
            'local': resultado.local_nome,
            'codigo': resultado.codigo,
            'descricao': resultado.descricao,
            'peca_fora_lista': resultado.peca_fora_lista,
            'quantidade_sistema': resultado.quantidade_sistema,
            'quantidade_real': resultado.quantidade_real,
            'diferenca': (
                resultado.quantidade_real - resultado.quantidade_sistema
                if resultado.quantidade_sistema is not None and resultado.quantidade_real is not None
                else None
            )
        })

    # Verifica se o usuário deseja o arquivo Excel
    if request.args.get('export') == 'excel':
        # Cria um DataFrame com os dados
        df = pd.DataFrame(comparacoes)

        # Gera o arquivo Excel em memória usando openpyxl
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Comparacoes')
        output.seek(0)

        # Envia o arquivo Excel
        return send_file(
            output,
            as_attachment=True,
            download_name='comparacoes.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    # Retorna os dados como JSON
    return jsonify(comparacoes)