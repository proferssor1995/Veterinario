from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy #SQLalchemy serve para manipular banco de dados

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELOS
class Tutor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
    data_hora = db.Column(db.String(100), nullable=False)
    veterinario = db.Column(db.String(100), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)

with app.app_context():
    db.create_all()

# ENDPOINTS

# Tutor
@app.route('/tutores', methods=['POST']) #Criar tutor
def criar_tutor():
    data = request.json
    novo = Tutor(nome=data['nome'])
    db.session.add(novo)
    db.session.commit()
    return jsonify({'id': novo.id, 'nome': novo.nome}), 201

@app.route('/tutores', methods=['GET']) #Consultar todos 
def listar_tutores():
    tutores = Tutor.query.all()
    return jsonify([{'id': t.id, 'nome': t.nome} for t in tutores])

@app.route('/tutores/<int:id>', methods=['GET'])  # Filtrar apenas pelo ID
def obter_tutor(id):
    tutor = Tutor.query.get_or_404(id)
    return jsonify({'id': tutor.id, 'nome': tutor.nome})

@app.route('/tutores/<string:nome_tutor>', methods=['GET']) #Pesquisar pelo nome ou sobrenome do tutor 
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

@app.route('/tutores/<int:id>', methods=['DELETE']) #Deletar apenas pelo ID
def deletar_tutor(id):
    tutor = Tutor.query.get_or_404(id)
    db.session.delete(tutor)
    db.session.commit()
    return jsonify({'mensagem': 'Tutor removido com sucesso'})

@app.route('/tutores/<int:id>', methods=['PUT']) #Alterar tutor com apenas ID que foi selecionado
def atualizar_tutor(id):
    tutor = Tutor.query.get_or_404(id)
    data = request.json
    tutor.nome = data.get('nome', tutor.nome)
    db.session.commit()
    return jsonify({'mensagem': 'Tutor atualizado com sucesso'})



# Animal
@app.route('/animais', methods=['POST'])
def criar_animal():
    data = request.json
    novo = Animal(
        nome=data['nome'],
        especie=data['especie'],
        tutor_id=data['tutor_id'])
    db.session.add(novo)
    db.session.commit()
    return jsonify({'id': novo.id}), 201

@app.route('/animais', methods=['GET']) #listar todos animais
def listar_animais():
    animais = Animal.query.all()
    return jsonify([
        {
            'id': a.id,
            'nome': a.nome,
            'especie': a.especie,
            'tutor': a.tutor.nome
        }
        for a in animais
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
    tutor = Tutor.query.filter_by(nome=nome_tutor).first()
    
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
    
@app.route('/animais/<string:nome_animal>', methods=['GET'])  # Pesquisar pelo nome do animal
def obter_nome_animal(nome_animal):
    animal = Animal.query.filter_by(nome=nome_animal).all()

    if not animal:
        abort(404, description='Animal não encontrado.')

    tutor = Tutor.query.get(animal.tutor_id)

    if not tutor:
        return {'mensagem': 'Nenhum animal encontrado para este tutor'}

    return {
        'id': animal.id,
        'nome': animal.nome,
        'especie': animal.especie,
        'tutor': tutor.nome
    }
    
@app.route('/animais/especie/<string:especie_animal>', methods=['GET'])
def obter_especie_animal(especie_animal):
    animais = Animal.query.filter_by(especie=especie_animal).all()
    
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


####Criar Endpoint de espeice de animal!! E colocar menos detalhe.
##Criar get de especie para que gerasse mais de um de especie
        
    
@app.route('/animais/<int:id>', methods=['DELETE']) #DELETAR apenas por ID
def deletar_animal(id):
    animal = Animal.query.get_or_404(id)
    db.session.delete(animal)
    db.session.commit()
    return jsonify({'mensagem': 'Animal removido com sucesso'})

@app.route('/animais/<int:id>', methods=['PUT']) #Alterar animal com apenas ID que foi selecionado
def atualizar_animal(id):
    animal = Animal.query.get_or_404(id)
    data = request.json
    animal.nome = data.get('nome', animal.nome)
    animal.especie = data.get('especie',animal.especie)
    db.session.commit()
    return jsonify({'mensagem': 'Animal atualizado com sucesso'})




# Agendamento
@app.route('/agendamentos', methods=['POST'])
def criar_agendamento():
    data = request.json
    novo = Agendamento(
        data_hora=data['data_hora'],
        veterinario=data['veterinario'],
        animal_id=data['animal_id']
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify({'id': novo.id}), 201

@app.route('/agendamentos', methods=['GET'])
def listar_agendamentos():
    ags = Agendamento.query.all()
    return jsonify([
        {
            'id': a.id,
            'data_hora': a.data_hora,
            'veterinario': a.veterinario,
            'animal': a.animal.nome,
            'tutor': a.animal.tutor.nome
        }
        for a in ags
    ])

@app.route('/agendamentos/<int:id>', methods=['DELETE'])
def deletar_agendamento(id):
    agendamento = Agendamento.query.get_or_404(id)
    db.session.delete(agendamento)
    db.session.commit()
    return jsonify({'mensagem': 'Agendamento removido com sucesso'})

@app.route('/agendamentos/<int:id>', methods=['PUT'])
def atualizar_agendamento(id):
    agendamento = Agendamento.query.get_or_404(id)
    data = request.json
    agendamento.data_hora = data.get('data_hora', agendamento.data_hora)
    agendamento.veterinario = data.get('veterinario', agendamento.veterinario)
    db.session.commit()
    return jsonify({'mensagem': 'Agendamento atualizado com sucesso'})


if __name__ == '__main__':
    app.run(debug=True)

##Consultar pelo postman

#POST /tutores Crir tutor
{
  "nome": "Maria Silva"
}

#POST /agendamentos criar agendamento
{
  "data_hora": "2025-06-14 10:00",
  "veterinario": "Dr. João",
  "animal_id": 1
}

#POST /animais cadastrar animal
{
  "nome": "Rex",
  "especie": "Cachorro",
  "tutor_id": 1
}


##Criar GET Para consultar pelo ID e Horario e DATA
## Criar DELETE para animal também