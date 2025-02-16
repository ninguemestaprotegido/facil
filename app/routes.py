from flask import Blueprint, session, render_template, request, redirect, url_for, send_file
from app.models import Importacao, Colaborador, db
from sqlalchemy import func
import datetime
from io import BytesIO
from openpyxl import Workbook

main = Blueprint('main', __name__)


# Página HOME (filtros, TOP 3, média)
@main.route('/', methods=['GET'])
def home():
    nome = request.args.get('nome', '').strip()
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')

    # Query inicial para resultados filtrados
    query = Importacao.query.join(Colaborador).add_columns(
    Importacao.id,  # Include the ID field
    Colaborador.nome,
    Importacao.data,
    Importacao.refile
)


    if nome:
        query = query.filter(Colaborador.nome.ilike(f"%{nome}%"))
    if data_inicial:
        query = query.filter(Importacao.data >= datetime.datetime.strptime(data_inicial, '%Y-%m-%d').date())
    if data_final:
        query = query.filter(Importacao.data <= datetime.datetime.strptime(data_final, '%Y-%m-%d').date())

    resultados = query.all()

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Calcular a média somente para os resultados filtrados
    media = sum(r.refile for r in resultados) / len(resultados) if resultados else None

    # TOP 3 com filtros aplicados
    top_melhores_filtrados = (
        db.session.query(Colaborador.nome, func.avg(Importacao.refile).label('media_refile'))
        .join(Importacao)
        .group_by(Colaborador.id)
        .order_by(func.avg(Importacao.refile).desc())
        .filter(
            Colaborador.nome.ilike(f"%{nome}%") if nome else True,
            Importacao.data >= datetime.datetime.strptime(data_inicial, '%Y-%m-%d').date() if data_inicial else True,
            Importacao.data <= datetime.datetime.strptime(data_final, '%Y-%m-%d').date() if data_final else True
        )
        .limit(3)
        .all()
    )

    top_piores_filtrados = (
        db.session.query(Colaborador.nome, func.avg(Importacao.refile).label('media_refile'))
        .join(Importacao)
        .group_by(Colaborador.id)
        .order_by(func.avg(Importacao.refile))
        .filter(
            Colaborador.nome.ilike(f"%{nome}%") if nome else True,
            Importacao.data >= datetime.datetime.strptime(data_inicial, '%Y-%m-%d').date() if data_inicial else True,
            Importacao.data <= datetime.datetime.strptime(data_final, '%Y-%m-%d').date() if data_final else True
        )
        .limit(3)
        .all()
    )

    # TOP 3 gerais (sem filtros)
    top_melhores_geral = (
        db.session.query(Colaborador.nome, func.avg(Importacao.refile).label('media_refile'))
        .join(Importacao)
        .group_by(Colaborador.id)
        .order_by(func.avg(Importacao.refile).desc())
        .limit(3)
        .all()
    )

    top_piores_geral = (
        db.session.query(Colaborador.nome, func.avg(Importacao.refile).label('media_refile'))
        .join(Importacao)
        .group_by(Colaborador.id)
        .order_by(func.avg(Importacao.refile))
        .limit(3)
        .all()
    )

    return render_template(
        'home.html',
        resultados=resultados,
        media=media,
        top_melhores_filtrados=top_melhores_filtrados,
        top_piores_filtrados=top_piores_filtrados,
        top_melhores_geral=top_melhores_geral,
        top_piores_geral=top_piores_geral,
    )


# Botao pra deletar coisas adicionadas de forma errada no home
@main.route('/delete/<int:id>', methods=['POST'])
def delete_result(id):
    # Get the record from the database
    resultado = Importacao.query.get_or_404(id)

    # Delete from database
    db.session.delete(resultado)
    db.session.commit()

    # Redirect back to home after deleting
    return redirect(url_for('main.home'))


# Exportação para Excel
@main.route('/exportar', methods=['GET'])
def exportar_excel():
    nome = request.args.get('nome')
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')

    query = Importacao.query.join(Colaborador).add_columns(
        Colaborador.nome, Importacao.data, Importacao.refile
    )

    if nome:
        query = query.filter(Colaborador.nome.ilike(f"%{nome}%"))
    if data_inicial:
        query = query.filter(Importacao.data >= datetime.datetime.strptime(data_inicial, '%Y-%m-%d'))
    if data_final:
        query = query.filter(Importacao.data <= datetime.datetime.strptime(data_final, '%Y-%m-%d'))

    resultados = query.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Importações"

    ws.append(["Data", "Funcionário", "Refile (%)"])

    for resultado in resultados:
        ws.append([
            resultado.data.strftime('%d/%m/%Y'),
            resultado.nome,
            resultado.refile
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="importacoes.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# Rota para colaboradores
@main.route('/colaboradores', methods=['GET', 'POST'])
def colaboradores():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cargo = request.form.get('cargo', '').strip()

        if not nome or not cargo:
            return redirect(url_for('main.colaboradores'))  # Impede cadastro vazio

        novo_colaborador = Colaborador(nome=nome, cargo=cargo)
        db.session.add(novo_colaborador)
        db.session.commit()

        return redirect(url_for('main.colaboradores'))

    colaboradores = Colaborador.query.order_by(Colaborador.id.desc()).all()
    return render_template('colaboradores.html', colaboradores=colaboradores)


# Editar colaborador
@main.route('/colaboradores/edit/<int:id>', methods=['GET', 'POST'])
def edit_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cargo = request.form.get('cargo', '').strip()

        if not nome or not cargo:
            return redirect(url_for('main.colaboradores'))  # Impede edição vazia

        colaborador.nome = nome
        colaborador.cargo = cargo
        db.session.commit()

        return redirect(url_for('main.colaboradores'))

    return render_template('edit_colaborador.html', colaborador=colaborador)


# Excluir colaborador
@main.route('/colaboradores/delete/<int:id>', methods=['POST'])
def delete_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)

    db.session.delete(colaborador)
    db.session.commit()

    return redirect(url_for('main.colaboradores'))


# Rota para importações
@main.route('/importacoes', methods=['GET', 'POST'])
def importacoes():
    if request.method == 'POST':
        data = request.form.get('data')
        funcionario_id = request.form.get('funcionario')
        refile = request.form.get('refile')

        if not data or not funcionario_id or not refile:
            return redirect(url_for('main.importacoes'))  # Impede cadastro inválido

        nova_importacao = Importacao(
            data=datetime.datetime.strptime(data, '%Y-%m-%d'),
            funcionario_id=int(funcionario_id),
            refile=float(refile)
        )
        db.session.add(nova_importacao)
        db.session.commit()

        return redirect(url_for('main.importacoes'))

    colaboradores = Colaborador.query.all()
    importacoes = Importacao.query.order_by(Importacao.data.desc()).all()
    return render_template('importacoes.html', colaboradores=colaboradores, importacoes=importacoes)
