from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pdfplumber
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = os.environ.get('SECRET_KEY', 'secret')
app.debug = os.environ.get('DEBUG', False)
app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')

db = SQLAlchemy(app)


class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255))
    tipo = db.Column(db.String(50))
    unidade_embalagem = db.Column(db.String(50))
    modal = db.Column(db.String(50))


def extract_selected_columns(pdf_path, selected_columns):
    table_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()

            # Assume que a primeira linha da tabela contém os cabeçalhos das colunas
            headers = table[1]
            col_indices = [headers.index(col) for col in selected_columns]

            for row in table[2:]:
                row_dict = {}
                for col_idx in col_indices:
                    header = headers[col_idx]
                    cell = row[col_idx]
                    row_dict[header] = cell
                table_data.append(row_dict)

    return table_data


@app.route('/', methods=['GET', 'POST'])
def index():
    produtos = Produto.query.all()
    return render_template('index.html', produtos=produtos)


@app.route('/produto/<int:produto_id>')
def detalhes_produto(produto_id):
    produtos = Produto.query.all()
    produto = Produto.query.get(produto_id)
    return render_template('detalhes_produto.html', produto=produto, produtos=produtos)


@app.route('/filtro', methods=['GET','POST'])
def filtro():
    produto_id = request.form.get('produto')
    produtos = Produto.query.all()  # Get all products
    produto = Produto.query.get(produto_id)
    return render_template('detalhes_produto.html', produtos=produtos, produto=produto)


@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    produtos = Produto.query.filter(Produto.nome.ilike(f'%{query}%')).all()
    result_list = [{'id': produto.id, 'nome': produto.nome, 'tipo': produto.tipo} for produto in produtos]
    return jsonify(result_list)


if __name__ == '__main__':
    with app.app_context():
        pdf_path = './precos4.pdf'
        selected_columns = ['PRODUTOS', 'TIPO', 'UNIDADE EMBALAGEM', 'MODAL']
        table_data = extract_selected_columns(pdf_path, selected_columns)
        db.create_all()
        for row_dict in table_data:
            # Verifica se o produto já existe no banco de dados
            existing_product = Produto.query.filter_by(nome=row_dict['PRODUTOS'],
                                                       tipo=row_dict['TIPO'],
                                                       unidade_embalagem=row_dict['UNIDADE EMBALAGEM'],
                                                       modal=row_dict['MODAL']).first()

            if not existing_product:
                produto = Produto(
                    nome=row_dict['PRODUTOS'],
                    tipo=row_dict['TIPO'],
                    unidade_embalagem=row_dict['UNIDADE EMBALAGEM'],
                    modal=row_dict['MODAL']
                )
                db.session.add(produto)
        db.session.commit()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
