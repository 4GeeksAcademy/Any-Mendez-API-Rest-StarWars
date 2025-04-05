"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Vehicle, Favorite
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


@app.route('/people', methods=['GET'])
def handle_people():
    try:
        people_list = []
        people = db.session.execute(db.select(People)).scalars().all()
        for ppl in people:
            people_list.append(ppl.serialize())

        return jsonify(people_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/people/<name>', methods=['GET'])
def handle_people_by_name(name):
    people = db.session.execute(
        db.select(People).filter_by(name=name)).scalar_one_or_none()

    if not None:
        return jsonify({"data": people.serialize()})


@app.route('/people/<int:people_id>', methods=['GET'])
def handle_people_by_id(people_id):
    people = db.session.execute(
        db.select(People).filter_by(id=people_id)).scalar_one_or_none()

    if people is not None:
        return jsonify(people.serialize())
    else:
        return jsonify({'response': f"No se encontro el personaje con el id{people_id}"}), 404


@app.route('/planets', methods=['GET'])
def handle_planet():
    try:
        planet_list = []
        planet = db.session.execute(db.select(Planet)).scalars().all()
        for pnt in planet:
            planet_list.append(pnt.serialize())

        return jsonify(planet_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/planets/<int:planets_id>', methods=['GET'])
def handle_planets_by_id(planets_id):
    planets = db.session.execute(
        db.select(Planet).filter_by(id=planets_id)).scalar_one_or_none()

    if planets is not None:
        return jsonify(planets.serialize())
    else:
        return jsonify({'response': f"No se encontro el planeta con el id{planets_id}"}), 404


@app.route('/users', methods=['GET'])
def handle_users():
    try:
        users_list = []
        users = db.session.execute(db.select(User)).scalars().all()
        for usr in users:
            users_list.append(usr.serialize())

        return jsonify(users_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/users/favorites', methods=['GET'])
def handle_users_fav():
    try:
        current_user_id = 1
        favorite_list = []
        favorites = db.session.execute(db.select(Favorite).filter_by(
            user_id=current_user_id)).scalars().all()
        for fvs in favorites:
            favorite_list.append(fvs.serialize())

        return jsonify(favorite_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_planet_favorites(planet_id):
    try:
        current_user_id = 1
        existing_favorite = db.session.execute(db.select(Favorite).filter_by(
            user_id=current_user_id, planet_id=planet_id)).scalars()

        if existing_favorite is None:
            return jsonify({'error': "El planeta ya esta en favoritos"}), 404

        new_favorite = Favorite(user_id=current_user_id, planet_id=planet_id)
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({'response': "Planeta agregado correctamente"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_people_favorites(people_id):
    try:
        current_user_id = 1
        existing_favorite = db.session.execute(db.select(Favorite).filter_by(
            user_id=current_user_id, people_id=people_id)).scalars()

        if existing_favorite is None:
            return jsonify({'error': "El personaje ya esta en favoritos"}), 404

        new_favorite = Favorite(user_id=current_user_id, people_id=people_id)
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({'response': "People agregado correctamente"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_planet_favorites(planet_id):
    try:
        current_user_id = 1
        favorite_to_delete = db.session.execute(db.select(Favorite).filter_by(
            user_id=current_user_id, planet_id=planet_id)).scalar()

        if favorite_to_delete is not None:
            db.session.delete(favorite_to_delete)
            db.session.commit()
            return jsonify({'response': "Planeta favorito eliminado correctamente"}), 200
        else:
            return jsonify({'response': "Planeta favorito no encontrado"}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_people_favorites(people_id):
    try:
        current_user_id = 1
        favorite_to_delete = db.session.execute(db.select(Favorite).filter_by(
            user_id=current_user_id, people_id=people_id)).scalar()

        if favorite_to_delete is not None:
            db.session.delete(favorite_to_delete)
            db.session.commit()
            return jsonify({'response': "Personaje favorito eliminado correctamente"}), 200
        else:
            return jsonify({'response': "Personaje favorito no encontrado"}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/planets', methods=['POST'])
def create_planet():
    try:
        data = request.get_json()

        if not data or 'name' not in data or 'diameter' not in data or 'population' not in data:
            return jsonify({'error': "Datos incompletos"}), 400

        new_planet = Planet(
            name=data['name'],
            diameter=data['diameter'],
            gravity=data['gravity'],
            climate=data['climate'],
            population=data['population']
        )

        db.session.add(new_planet)
        db.session.commit()

        return jsonify({'response': 'Planeta creado correctamente'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/people', methods=['POST'])
def create_people():
    try:
        data = request.get_json()

        if not data or 'name' not in data or 'birth_year' not in data or 'eye_color' not in data:
            return jsonify({'error': "Datos incompletos"}), 400

        new_people = People(
            name=data['name'],
            birth_year=data['birth_year'],
            eye_color=data['eye_color'],
            gender=data['gender'],
            hair_color=data['hair_color'],
            height=data['height']
        )

        db.session.add(new_people)
        db.session.commit()

        return jsonify({'response': 'Personaje creado correctamente'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/planets/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id):
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': "Datos incompletos"}), 400

        planet_to_update = db.session.execute(
            db.select(Planet).filter_by(id=planet_id)).scalar()

        if planet_to_update:

            if 'name' in data:
                planet_to_update.name = data['name']
            if 'diameter' in data:
                planet_to_update.diameter = data['diameter']
            if 'gravity' in data:
                planet_to_update.gravity = data['gravity']
            if 'climate' in data:
                planet_to_update.climate = data['climate']
            if 'population' in data:
                planet_to_update.population = data['population']

            db.session.commit()
            return jsonify({'response': 'Planeta actualizado correctamente'}), 200
        else:
            return jsonify({'response': 'Planeta no encontrado'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/people/<int:people_id>', methods=['PUT'])
def update_people(people_id):
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': "Datos incompletos"}), 400

        people_to_update = db.session.execute(
            db.select(People).filter_by(id=people_id)).scalar()

        if people_to_update:

            if 'name' in data:
                people_to_update.name = data['name']
            if 'birth_year' in data:
                people_to_update.birth_year = data['birth_year']
            if 'eye_color' in data:
                people_to_update.eye_color = data['eye_color']
            if 'gender' in data:
                people_to_update.gender = data['gender']
            if 'hair_color' in data:
                people_to_update.hair_color = data['hair_color']
            if 'height' in data:
                people_to_update.height = data['height']

            db.session.commit()
            return jsonify({'response': 'Personaje actualizado correctamente'}), 200
        else:
            return jsonify({'response': 'Personaje no encontrado'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_people(people_id):
    try:
        # Buscar la persona
        people_to_delete = db.session.execute(
            db.select(People).filter_by(id=people_id)).scalar()

        if people_to_delete:
            db.session.delete(people_to_delete)
            db.session.commit()
            return jsonify({'response': 'Personaje eliminado correctamente'}), 200
        else:
            return jsonify({'response': 'Personaje no encontrado'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    try:
        # Buscar el planeta
        planet_to_delete = db.session.execute(
            db.select(Planet).filter_by(id=planet_id)).scalar()

        if planet_to_delete:
            db.session.delete(planet_to_delete)
            db.session.commit()
            return jsonify({'response': 'Planeta eliminado correctamente'}), 200
        else:
            return jsonify({'response': 'Planeta no encontrado'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
