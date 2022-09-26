import atexit

from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy import Column, Integer, String, DateTime, func, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker


DSN = "postgresql://app:1234@127.0.0.1:5431/netology_flask"

engine = create_engine(DSN)
Session = sessionmaker(bind=engine)

app = Flask("server")
Base = declarative_base()
atexit.register(lambda: engine.dispose())


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key = True)
    nickname = Column(String(50), unique = True, nullable=False)
    advs = relationship("Adv", backref='owner')



class Adv(Base):
    __tablename__ = "adv"

    id = Column(Integer, primary_key = True)
    title = Column(String(50), nullable=False)
    desc = Column(String)
    owner_id = Column(Integer, ForeignKey("user.id"))
    #user = relationship(User)
    created_at = Column(DateTime, server_default=func.now())



Base.metadata.create_all(engine)

class AdvView(MethodView):
    def get(self):
        return jsonify({})

    def post(self):
        json_data = request.json
        with Session() as session:
            new_adv = Adv(**json_data)
            session.add(new_adv)
            session.commit()

            return jsonify({"status": "success", "id": new_adv.id})

    def patch(self):
        return jsonify({})

    def delete(self):
        return jsonify({})


# def test():
#     data = request.json
#     headers = request.headers
#     qs = request.args
#
#
#     return jsonify({"Hello": "World", "json": data, "headers": dict(headers), "qs": dict(qs)})

# app.add_url_rule("/test/", view_func=test)

app.add_url_rule("/advs/", methods=["POST"], view_func=AdvView.as_view("create_adv"))
app.run(debug=True)