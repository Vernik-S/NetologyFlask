import atexit
from typing import Union, Optional

from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy import Column, Integer, String, DateTime, func, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
import pydantic

DSN = "postgresql://app:1234@127.0.0.1:5431/netology_flask"

engine = create_engine(DSN)
Session = sessionmaker(bind=engine)

app = Flask("server")
Base = declarative_base()
atexit.register(lambda: engine.dispose())


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    nickname = Column(String(50), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)

    advs = relationship("Adv", backref='owner')


class Adv(Base):
    __tablename__ = "adv"

    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    desc = Column(String)
    owner_id = Column(Integer, ForeignKey("user.id"))
    # user = relationship(User)
    created_at = Column(DateTime, server_default=func.now())


Base.metadata.create_all(engine)


class HTTPError(Exception):
    def __init__(self, status_code: int, message: Union[str, list, dict]):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HTTPError)
def handle_invalid_usage(error):
    response = jsonify({"message": error.message})
    response.status_code = error.status_code
    return response


def get_user(user_name: str, session: Session) -> User:
    user = session.query(User).filter(User.nickname == user_name).first()
    if user is None:
        raise HTTPError(400, f"user {user_name} not found ")
    return user


# убрать дублирование get?
def get_adv(adv_id: int, session: Session) -> Adv:
    adv = session.query(Adv).get(adv_id)
    if adv is None:
        raise HTTPError(400, f"adv_id {adv_id} not found ")
    return adv


class CreateAdvSchema(pydantic.BaseModel):
    title: str
    desc: str
    owner: str

    @pydantic.validator("title")
    def check_title(cls, value):
        if len(value) <= 10:
            raise ValueError("title is too short")
        elif len(value) > 50:
            raise ValueError("title is too long")
        return value


class UpdateAdvSchema(pydantic.BaseModel):
    title: Optional[str]
    desc: Optional[str]

    # owner: Optional[str] #При патче владельца менять нельзя. Таким образом, owner в validated_data не будет

    @pydantic.validator("title")
    def check_title(cls, value):
        if len(value) <= 10:
            raise ValueError("title is too short")
        elif len(value) > 50:
            raise ValueError("title is too long")

        return value


def validate(Schema, data: dict):
    try:
        data_validated = Schema(**data).dict(exclude_none=True)
    except pydantic.ValidationError as er:
        raise HTTPError(400, er.errors())
    return data_validated


class AdvView(MethodView):
    def get(self, adv_id: int):
        with Session() as session:
            adv = get_adv(adv_id, session)
            owner = session.query(User).get(adv.owner_id)

        # return jsonify(**dict(adv)) #Можно ли распаковать?

        return jsonify(
            {"title": adv.title, "description": adv.desc, "owner": owner.nickname,
             "created_at": adv.created_at.isoformat()})

    def post(self):
        json_data_validated = validate(CreateAdvSchema, request.json)

        with Session() as session:
            user_name = json_data_validated.pop("owner")
            user = get_user(user_name, session)
            json_data_validated["owner_id"] = user.id
            new_adv = Adv(**json_data_validated)
            session.add(new_adv)
            session.commit()

            return jsonify({"status": "success", "id": new_adv.id})

    def patch(self, adv_id: int):
        json_data_validated = validate(UpdateAdvSchema, request.json)
        with Session() as session:
            adv = get_adv(adv_id, session)

            for key, value in json_data_validated.items():
                setattr(adv, key, value)
            session.add(adv)
            session.commit()

            return jsonify(
                {"title": adv.title, "description": adv.desc})

    def delete(self, adv_id: int):
        with Session() as session:
            adv = get_adv(adv_id, session)
            session.delete(adv)
            session.commit()

        return jsonify(f"Adv wit id {adv_id} deleted")


# def test():
#     data = request.json
#     headers = request.headers
#     qs = request.args
#
#
#     return jsonify({"Hello": "World", "json": data, "headers": dict(headers), "qs": dict(qs)})

# app.add_url_rule("/test/", view_func=test)

app.add_url_rule("/advs/", methods=["POST"], view_func=AdvView.as_view("create_adv"))
app.add_url_rule("/advs/<int:adv_id>", methods=["GET", "PATCH", "DELETE"], view_func=AdvView.as_view("get_adv"))
app.run(debug=True)
