from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
import random

API_KEY = "TopSecretAPIKey"
API_DOCUMENTATION_URL = "https://documenter.getpostman.com/view/35996843/2sA3Qy6pgY"

app = Flask(__name__)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        # LOOPS INTO EACH COLUMN OF THE DB OR DATA RECORDS - METHOD 1
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary

        # LOOPS INTO EACH COLUMN OF THE DB OR DATA RECORDS - METHOD 2 (DICTIONARY COMPREHENSION)
        # return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()
    cafes_list = [cafe.to_dict() for cafe in all_cafes]
    return render_template('index.html', cafes=cafes_list)


@app.route('/search')
def get_cafes_by_location():
    query_location = request.args.get("loc")
    result = db.session.execute(db.select(Cafe).where(Cafe.location == query_location))
    all_cafes = result.scalars().all()
    if all_cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])
    else:
        return jsonify(error={
            "Not found": "Sorry we don't have a cafe at that location"
        }), 404


# HTTP POST - Create Record
# @app.route('/add', methods=["POST"])
# def post_new_cafe():
#     new_cafe = Cafe(
#         name=request.form.get("name"),
#         map_url=request.form.get("map_url"),
#         img_url=request.form.get("img_url"),
#         location=request.form.get("loc"),
#         has_sockets=bool(request.form.get("sockets")),
#         has_toilet=bool(request.form.get("toilet")),
#         has_wifi=bool(request.form.get("wifi")),
#         can_take_calls=bool(request.form.get("calls")),
#         seats=request.form.get("seats"),
#         coffee_price=request.form.get("coffee_price"),
#     )
#     db.session.add(new_cafe)
#     db.session.commit()
#     return jsonify(response={"success": "Successfully added the new cafe."})
# HTTP POST - Create Record
@app.route('/add', methods=["GET", "POST"])
def post_new_cafe():
    if request.method == "POST":
        # Ottieni i dati dal form come hai fatto prima
        name = request.form.get("name")
        map_url = request.form.get("map_url")
        img_url = request.form.get("img_url")
        location = request.form.get("loc")
        has_sockets = bool(request.form.get("sockets"))
        has_toilet = bool(request.form.get("toilet"))
        has_wifi = bool(request.form.get("wifi"))
        can_take_calls = bool(request.form.get("calls"))
        seats = request.form.get("seats")
        coffee_price = request.form.get("coffee_price")

        # Validazione dei dati (esempio: verifica che il nome non sia vuoto)
        if not name:
            return jsonify(error="Name is required."), 400

        # Crea un nuovo oggetto Cafe
        new_cafe = Cafe(
            name=name,
            map_url=map_url,
            img_url=img_url,
            location=location,
            has_sockets=has_sockets,
            has_toilet=has_toilet,
            has_wifi=has_wifi,
            can_take_calls=can_take_calls,
            seats=seats,
            coffee_price=coffee_price,
        )

        # Aggiungi il nuovo cafe al database
        try:
            db.session.add(new_cafe)
            db.session.commit()
            return jsonify(success="Successfully added the new cafe.")
        except Exception as e:
            db.session.rollback()
            return jsonify(error=f"Failed to add the new cafe: {str(e)}"), 500

    # Se il metodo HTTP è GET, mostra il template add.html
    return render_template('add.html')


# HTTP PUT/PATCH - Update Record
@app.route('/update/<int:cafe_id>', methods=['GET', 'POST'])
def update_price(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)
    if not cafe:
        return jsonify(error={"Not Found": "Cafe id not found in the database"}), 404

    if request.method == 'POST':
        if request.form.get('_method') == 'PATCH':
            new_price = request.form.get("coffee_price")

            if new_price:
                cafe.coffee_price = new_price
                try:
                    db.session.commit()
                    # return jsonify(response={"success": "Coffee price updated successfully"}), 200
                    return redirect(url_for('home'))
                except Exception as e:
                    db.session.rollback()
                    return jsonify(error={"Database Error": str(e)}), 500
            else:
                return jsonify(error={"Bad Request": "New price not provided"}), 400

    return render_template('update.html', cafe=cafe)


# HTTP DELETE - Delete Record
@app.route('/report-close/<int:cafe_id>', methods=['DELETE'])
def delete_cafe(cafe_id):
    cafe = db.get_or_404(Cafe, cafe_id)
    api_key = request.args.get("api-key")
    if cafe:
        if api_key == API_KEY:
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(response={"success": "Cafe closing reported successfully"}), 200
        else:
            return jsonify(error={"Forbidden": "Sorry, you're not allowed to perform this action"}), 403
    else:
        return jsonify(error={"Not Found": "Cafe id not found in the database"}), 404


if __name__ == '__main__':
    app.run(debug=True)
