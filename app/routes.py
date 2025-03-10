from flask import Blueprint, session, render_template, request, redirect, url_for, send_file
from app.models import Importacao, Colaborador, db, User
from sqlalchemy import func
import datetime
from io import BytesIO
from openpyxl import Workbook
import pandas as pd
from flask import send_file
import os

main = Blueprint('main', __name__)

# Página HOME (filtros, TOP 3, média)
@main.route('/', methods=['GET'])
def home():
    nome = request.args.get('nome', '').strip()
    cargo = request.args.get('cargo', '').strip()
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    ordenar = request.args.get('ordenar', 'desc')  # Ordenação padrão descendente

    # Query base para médias
    query = db.session.query(
        Colaborador.nome,
        Colaborador.cargo,
        func.avg(Importacao.refile).label('media_refile')
    ).join(Importacao).group_by(Colaborador.id)

    # Aplicar filtros
    if nome:
        query = query.filter(Colaborador.nome.ilike(f"%{nome}%"))
    if cargo:
        query = query.filter(Colaborador.cargo.ilike(f"%{cargo}%"))
    if data_inicial:
        query = query.filter(Importacao.data >= datetime.datetime.strptime(data_inicial, '%Y-%m-%d').date())
    if data_final:
        query = query.filter(Importacao.data <= datetime.datetime.strptime(data_final, '%Y-%m-%d').date())

    # Aplicar ordenação
    if ordenar == 'asc':
        query = query.order_by(func.avg(Importacao.refile).asc())
    else:
        query = query.order_by(func.avg(Importacao.refile).desc())

    medias_colaboradores = query.all()

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        

        
        
    # Cálculo da média geral
    media = sum([c.media_refile for c in medias_colaboradores]) / len(medias_colaboradores) if medias_colaboradores else None

    # Calcular Top 3 e Last 3 aplicando os mesmos filtros
    top_3 = medias_colaboradores[:3]
    last_3 = medias_colaboradores[-3:]

    return render_template(
        'home.html',
        medias_colaboradores=medias_colaboradores,
        media=media,
        top_3=top_3,
        last_3=last_3,
        ordenar=ordenar
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
@main.route('/exportar_excel', methods=['GET'])
def exportar_excel():
    nome = request.args.get('nome', '').strip()
    cargo = request.args.get('cargo', '').strip()
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')

    # Query base
    query = db.session.query(
        Colaborador.nome,
        Colaborador.cargo,
        func.avg(Importacao.refile).label('media_refile')
    ).join(Importacao).group_by(Colaborador.id)

    # Aplicar filtros
    if nome:
        query = query.filter(Colaborador.nome.ilike(f"%{nome}%"))
    if cargo:
        query = query.filter(Colaborador.cargo.ilike(f"%{cargo}%"))
    if data_inicial:
        query = query.filter(Importacao.data >= datetime.datetime.strptime(data_inicial, '%Y-%m-%d').date())
    if data_final:
        query = query.filter(Importacao.data <= datetime.datetime.strptime(data_final, '%Y-%m-%d').date())

    # Obter resultados
    resultados = query.all()

    # Converter para DataFrame
    data = [{
        'Funcionário': r.nome,
        'Cargo': r.cargo,
        'Média Refile (%)': round(r.media_refile, 2)
    } for r in resultados]

    df = pd.DataFrame(data)

    # Salvar o Excel no caminho absoluto
    output_folder = os.path.join(os.getcwd(), 'app')  # Garante que será salvo no diretório do app
    file_path = os.path.join(output_folder, 'export_resumo_resultados.xlsx')
    df.to_excel(file_path, index=False)

    # Enviar o arquivo para download
    return send_file(file_path, as_attachment=True)

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
    data_selecionada = ''
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

        data_selecionada = data  # Armazena a data selecionada

    colaboradores = Colaborador.query.all()
    importacoes = Importacao.query.order_by(Importacao.data.desc()).all()
    return render_template('importacoes.html', colaboradores=colaboradores, importacoes=importacoes, data_selecionada=data_selecionada)


#rota para a nova guia "Feedback Funcionário"
@main.route('/feedback', methods=['GET'])
def feedback_funcionario():
    nome = request.args.get('nome', '').strip()
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')

    # Query inicial para resultados filtrados
    query = Importacao.query.join(Colaborador).add_columns(
        Importacao.id,
        Colaborador.nome,
        Colaborador.cargo,
        Importacao.data,
        Importacao.refile
    )

    # Filtros aplicados
    if nome:
        query = query.filter(Colaborador.nome.ilike(f"%{nome}%"))
    if data_inicial:
        query = query.filter(Importacao.data >= datetime.datetime.strptime(data_inicial, '%Y-%m-%d').date())
    if data_final:
        query = query.filter(Importacao.data <= datetime.datetime.strptime(data_final, '%Y-%m-%d').date())

    resultados = query.all()

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Calcular a média dos resultados filtrados
    media = sum(r.refile for r in resultados) / len(resultados) if resultados else None

    return render_template(
        'feedback.html',
        resultados=resultados,
        media=media
    )

