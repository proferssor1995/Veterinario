from flask import Flask, request, jsonify, abort #abort serve para dar alert 404
from flask_sqlalchemy import SQLAlchemy #SQLalchemy serve para manipular banco de dados
from datetime import datetime #Datetime serve para identificar ano, mes, dia, hora, minuto e segundos
from sqlalchemy import func
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELOS
class Tutor(db.Model):
    id = db.Column(db.Integer, primary_key=True) #Integer serve para que criasse ID automaticamente
    nome = db.Column(db.String(100), nullable=False)
    animais = db.relationship('Animal', backref='tutor', lazy=True) #backref um string que faz parte para vários chaves

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(50), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor.id'), nullable=False)
    agendamentos = db.relationship('Agendamento', backref='animal', lazy=True)

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False)
    veterinario = db.Column(db.String(100), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)

with app.app_context():
    db.create_all()

# ENDPOINTS para filtrar mais pesquisa como; tutores, animais, id, agendamento, nome do veterinario

# Tutor
@app.route('/tutores', methods=['POST']) #Criar tutor com nome
def criar_tutor():
    data = request.json
    novo = Tutor(nome=data['nome'])
    db.session.add(novo)
    db.session.commit()
    return jsonify({'id': novo.id, 'nome': novo.nome}), 201

@app.route('/tutores/id/<int:id>', methods=['POST'])
def criar_tutor_id(id):
    data = request.json

    # Verifica se o ID já está em uso
    tutor_existente = Tutor.query.get(id)
    if tutor_existente:
        return jsonify({'erro': f'O ID {id} já está em uso.'}), 400

    # Cria um novo tutor com o ID especificado
    novo = Tutor(id=id, nome=data['nome'])

    db.session.add(novo)
    db.session.commit()

    return jsonify({'id': novo.id, 'nome': novo.nome}), 201

@app.route('/tutores', methods=['GET']) #Consultar todos 
def listar_tutores():
    tutores = Tutor.query.all()
    return jsonify([
        {
            'id': t.id,
            'nome': t.nome,
        } for t in tutores
        ])

@app.route('/tutores/id/<int:id>', methods=['GET'])  # Filtrar apenas pelo ID do tutor
def obter_tutor(id):
    tutor = Tutor.query.get_or_404(id)
    return jsonify({
        'id': tutor.id, 
        'nome': tutor.nome
        })

@app.route('/tutores/nome/<string:nome_tutor>', methods=['GET']) #Pesquisar pelo nome ou sobrenome do tutor 
def obter_tutor_nome(nome_tutor):
    tutor = Tutor.query.filter(Tutor.nome.ilike(f'%{nome_tutor}%')).first()
    
    if not tutor:
        abort(404, description='Tutor não encontrado.')
    
    animais = Animal.query.filter_by(tutor_id=tutor.id).all()
    
    if not animais:
        return({'mensagem':'Nenhum tutor encontrado'})
    
    return jsonify([
        {
        'id':animal.id,
        'nome':animal.nome,
        'especie':animal.especie,
        'tutor':tutor.nome
        } for animal in animais
        ])

@app.route('/tutores/id/<int:id>', methods=['DELETE']) #Deletar apenas pelo ID
def deletar_tutor(id):
    tutor = Tutor.query.get_or_404(id)
    db.session.delete(tutor)
    db.session.commit()
    return jsonify({'mensagem': 'Tutor removido com sucesso'})

@app.route('/tutores/id/<int:id>', methods=['PUT']) #Alterar tutor com apenas ID que foi selecionado, alterar apenas nome do Tutor
def atualizar_tutor(id):
    tutor = Tutor.query.get_or_404(id)
    data = request.json
    tutor.nome = data.get('nome', tutor.nome)
    db.session.commit()
    return jsonify({'mensagem': 'Tutor atualizado com sucesso'})

#### Fazer DELETE,PUT e POST com apenas ID por ser chave primária, ou seja, chave única


# Animal
@app.route('/animais', methods=['POST']) #Adicionar informação do animal, como nome, especie e ID do tutor
def criar_animal():
    data = request.json
    novo = Animal(
        nome=data['nome'],
        especie=data['especie'],
        tutor_id=data['tutor_id'])
    db.session.add(novo)
    db.session.commit()
    return jsonify({'id': novo.id}), 201

@app.route('/animais/id/<int:id>', methods=['POST'])
def criar_animal_id(id):
    data = request.json

    # Verificar se os campos obrigatórios estão presentes
    if 'nome' not in data or 'especie' not in data:
        return jsonify({'erro': 'Campos "nome" e "especie" são obrigatórios'}), 400

    # Verificar se o ID já está em uso
    animal_existente = Animal.query.get(id)
    if animal_existente:
        return jsonify({'erro': f'O ID {id} já está em uso'}), 400

    # Criar um novo animal com o ID especificado
    novo = Animal(
        id=id,
        nome=data['nome'],
        especie=data['especie']
    )

    # Verificar se o tutor_id deve ser atribuído (se necessário)
    if 'tutor_id' in data:
        novo.tutor_id = data['tutor_id']

    db.session.add(novo)
    db.session.commit()

    # Retornar o animal criado
    return jsonify({
        'id': novo.id,
        'nome': novo.nome,
        'especie': novo.especie,
        'tutor_id': novo.tutor_id if hasattr(novo, 'tutor_id') else None
    }), 201

@app.route('/animais', methods=['GET'])
def listar_animais():
    animais = Animal.query.options(joinedload(Animal.tutor)).all() #Já traz os animais com os tutores juntos em única consulta
    return jsonify([
        {
            'id': a.id,
            'nome': a.nome,
            'especie': a.especie,
            'tutor': a.tutor.nome if a.tutor else None # Se não estiver tutor, mesmo assim vai gerar consulta
        } for a in animais
    ])
    
@app.route('/animais/id/<int:id>', methods=['GET']) #Obter dado do animal pelo ID
def obter_animal(id):
    animal = Animal.query.get_or_404(id)
    return({
        'id':animal.id,
        'nome':animal.nome,
        'especie':animal.especie,
        'tutor':animal.tutor.nome
    })
    
@app.route('/animais/tutores/<string:nome_tutor>', methods = ['GET']) #Pesquisar pelo nome do tutor do animal
def obter_tutor_animal(nome_tutor):
    tutor = Tutor.query.filter(Tutor.nome.ilike(f'%{nome_tutor}%')).first()
    
    if not tutor:
        abort(404, description='Tutor não encontrado.')
    
    animais = Animal.query.filter_by(tutor_id=tutor.id).all()
    
    if not animais:
        return({'mensagem':'Nenhum tutor encontrado para este animal'})
    
    return([
        {
        'id':animal.id,
        'nome':animal.nome,
        'especie':animal.especie,
        'tutor':tutor.nome
        } for animal in animais
        ])
    
@app.route('/animais/nome/<string:nome_animal>', methods=['GET'])  # Pesquisar pelo nome do animal
def obter_nome_animal(nome_animal):
    animais = Animal.query.filter(Animal.nome.ilike(f'%{nome_animal}%')).all()

    if not animais:
        abort(404, description='Animal não encontrado.')

    return jsonify([
        {
        'id': animal.id,
        'nome': animal.nome,
        'especie': animal.especie,
        'tutor': Tutor.query.get(animal.tutor_id).nome if Tutor.query.get(animal.tutor_id) else 'Tutor não encontrado'
        } for animal in animais
        ])
    
@app.route('/animais/especie/<string:especie_animal>', methods=['GET']) #Pesquisar pelo especie do animal
def obter_especie_animal(especie_animal):
    animais = Animal.query.filter(Animal.especie.ilike(f'%{especie_animal}%')).all()
    
    if not animais:
        abort(404, description='Espécie não encontrada.')  

    return [
        {
            'id': animal.id,
            'nome': animal.nome,
            'especie': animal.especie,
            'tutor': Tutor.query.get(animal.tutor_id).nome if Tutor.query.get(animal.tutor_id) else 'Sem tutor'
        }
        for animal in animais
    ]
    
@app.route('/animais/id/<int:id>', methods=['DELETE'])
def deletar_animal_id(id):
    try:
        animal = Animal.query.get_or_404(id)
        db.session.delete(animal)
        db.session.commit()
        return jsonify({'mensagem': 'Animal removido com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao deletar o animal', 'detalhes': str(e)}), 500


@app.route('/animais/nome/<string:nome_animal>', methods=['DELETE']) #Remover nome do animal pelo nome certinho
def deletar_animal_nome(nome_animal):
    animal = Animal.query.get_or_404(nome_animal)
    db.session.delete(animal)
    db.session.commit()
    return jsonify({'Animal foi removido com sucesso.'})



@app.route('/animais/id/<int:id>', methods=['PUT']) #Alterar animal com apenas ID que foi selecionado, e alterar nome e especie do animal
def atualizar_animal(id):
    animal = Animal.query.get_or_404(id)
    data = request.json
    animal.nome = data.get('nome', animal.nome)
    animal.especie = data.get('especie',animal.especie)
    db.session.commit()
    return jsonify({'mensagem': 'Animal atualizado com sucesso'})




# Agendamento
@app.route('/agendamentos', methods=['POST'])  # Adicionar consulta, colocando data e horário, nome do veterinário e ID do animal
def criar_agendamento():
    data = request.json
    
    try:
        data_convertida = datetime.strptime(data['data_hora'], '%d-%m-%Y %H:%M')
    except ValueError:
        return jsonify({'erro': 'Formato de data/hora inválido. Use DD-MM-AAAA HH:MM'}), 400

    novo = Agendamento(
        data_hora=data_convertida,
        veterinario=data['veterinario'],
        animal_id=data['animal_id']
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify({'id': novo.id}), 201

@app.route('/agendamentos/id/<int:id>', methods=['POST'])
def criar_agendamento_id(id):
    data = request.json

    # Verificar se o ID já está em uso
    agendamento_existente = Agendamento.query.get(id)
    if agendamento_existente:
        return jsonify({'erro': f'O ID {id} já está em uso'}), 400

    # Validar e converter data/hora
    try:
        data_hora_formatada = datetime.strptime(data['data_hora'], '%d-%m-%Y %H:%M')
    except ValueError:
        return jsonify({'erro': 'Formato de data/hora inválido. Use DD-MM-AAAA HH:MM'}), 400

    # Criar novo agendamento
    novo = Agendamento(
        id=id,
        data_hora=data_hora_formatada,
        veterinario=data['veterinario'],
        animal_id=data['animal_id']
    )

    db.session.add(novo)
    db.session.commit()

    return jsonify({
        'id': novo.id,
        'data_hora': novo.data_hora.strftime('%d-%m-%Y %H:%M'),
        'veterinario': novo.veterinario
    }), 201
###### Verificar se agendamento de POST funciona ou não

@app.route('/agendamentos', methods=['GET']) ## mostrar todas agendas, por ordem de ID
def listar_agendamentos():
    ags = Agendamento.query.all()
    return jsonify([
        {
            'id': a.id,
            'data_hora': a.data_hora,
            'veterinario': a.veterinario,
            'animal': a.animal.nome,
            'especie':a.animal.especie,
            'tutor': a.animal.tutor.nome
        }
        for a in ags
    ])

@app.route('/agendamentos/data_hora/<string:data>', methods=['GET'])
def listar_data(data):
    try:
        # Converter a string para data (sem hora)
        data_formatada = datetime.strptime(data, '%d-%m-%Y').date()

        # Filtrar pela parte da data de data_hora
        agendamentos = Agendamento.query.filter(
            func.date(Agendamento.data_hora) == data_formatada
        ).all()

        if not agendamentos:
            abort(404, description='Data não encontrada')

        return jsonify([
            {
                'id': ag.id,
                'data_hora': ag.data_hora.strftime('%d-%m-%Y %H:%M'),
                'veterinario': ag.veterinario,
                'animal': ag.animal.nome,
                'especie':ag.animal.espcie,
                'tutor': ag.animal.tutor.nome
            } for ag in agendamentos
        ])
    
    except ValueError:
        return jsonify({'erro': 'Formato inválido. Use DD-MM-AAAA'}), 400
    
@app.route('/agendamentos/veterinario/<string:nome_veterinario>', methods=['GET']) #Consultar agendamento do Veterinario pelo nome
def procurar_veterinario(nome_veterinario):
    veterinario = Agendamento.query.filter(Agendamento.veterinario.ilike(f'%{nome_veterinario}%')).all()
    if not veterinario:
        abort(404, discription='Veterináio não encontrado')
        
    return jsonify([
        {
            'id': v.id,
            'data_hora': v.data_hora,
            'veterinario': v.veterinario,
            'animal': v.animal.nome,
            'especie':v.animal.especie,
            'tutor': v.animal.tutor.nome
        } for v in veterinario
    ])
    
@app.route('/agendamentos/id/<int:id>', methods=['GET']) #filtrar consulta pelo ID
def procurar_pelo_id(id):
    agendamento = Agendamento.query.get_or_404(id)
    return jsonify(
        {
            'id': agendamento.id,
            'data_hora': agendamento.data_hora,
            'veterinario': agendamento.veterinario,
            'animal': agendamento.animal.nome,
            'especie':agendamento.animal.especie,
            'tutor': agendamento.animal.tutor.nome
        }
    )

@app.route('/agendamentos/id/<int:id>', methods=['DELETE'])
def deletar_agendamento(id):
    agendamento = Agendamento.query.get_or_404(id)
    db.session.delete(agendamento)
    db.session.commit()
    return jsonify({'mensagem': 'Agendamento removido com sucesso'})

@app.route('/agendamentos/id/<int:id>', methods=['PUT']) #Permitindo alterar desde data e hora, tutores, veterianrio, especie de animal e nome do animal
def atualizar_agendamento_completo(id):
    agendamento = Agendamento.query.get_or_404(id)
    data = request.json

    # Atualizar data_hora
    if 'data_hora' in data:
        try:
            agendamento.data_hora = datetime.strptime(data['data_hora'], '%d-%m-%Y %H:%M')
        except ValueError:
            return jsonify({'erro': 'Formato de data/hora inválido. Use DD-MM-AAAA HH:MM'}), 400

    # Atualizar nome do veterinário
    if 'veterinario' in data:
        agendamento.veterinario = data['veterinario']

    # Atualizar dados do animal (relacionado ao agendamento)
    if 'animal' in data:
        animal = agendamento.animal
        animal.nome = data['animal'].get('nome', animal.nome)
        animal.especie = data['animal'].get('especie', animal.especie)

    # Atualizar dados do tutor (relacionado ao animal)
    if 'tutor' in data:
        tutor = agendamento.animal.tutor
        tutor.nome = data['tutor'].get('nome', tutor.nome)

    # Atualizar dados do veterinario ( relacionado ao veterinario)

    db.session.commit()
    return jsonify({'mensagem': 'Agendamento (e dados relacionados) atualizado com sucesso'})


if __name__ == '__main__':
    app.run(debug=True)

##Consultar pelo postman

#POST /tutores Criar tutor
{
  "nome": "Maria Silva"
}

#POST /agendamentos criar agendamento
{
  "data_hora": "14-06-2025 10:00",
  "veterinario": "Dr. João",
  "animal_id": 1
}

#POST /animais cadastrar animal
{
  "nome": "Rex",
  "especie": "Cachorro",
  "tutor_id": 1
}

#PUT para alterar agendamento
{
  "data_hora": "25-07-2025 16:00",
  "veterinario": "Dr. Francisco",
  "animal": {
    "nome": "Yuna",
    "especie": "Gato"
  },
  "tutor": {
    "nome": "Fernando"
  }
}

##Devo criar endpoint só de veterinário? Não porque gera dados semelhança agendamento
#Analisar porque mesmo fazendo PUT, na hora de consultar pelo agendamento não está funcionando

#Pousar codigo na hora de debugar.
#Analisar em breakpoint, para saber como está executando