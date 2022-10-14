import atexit
from typing import Union, Optional

from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy import Column, Integer, String, DateTime, func, create_engine, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
import pydantic
import base64
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_httpauth import HTTPBasicAuth
from flask import g

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
    password_hash = Column(String(128))
    # password = Column(String(128))
    is_admin = Column(String, nullable=False, default=False)

    token = Column(String(32), index=True, unique=True)
    token_expiration = Column(DateTime)

    advs = relationship("Adv", backref='owner')

    def get_token(self, session, expires_in=3600, ):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        session.add(self)

        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


basic_auth = HTTPBasicAuth()


#     with Session() as session:
#         test_user1 = User(nickname="TestUser1", email="a1@a.a", password_hash=generate_password_hash("1234"))
#         test_user2 = User(nickname="TestUsr2", email="a2@a.a", password_hash=generate_password_hash("5678"))
#         test_admin = User(nickname="TestAdmin", email="a3@a.a", password_hash=generate_password_hash("0007"), is_admin=True)
#         session.add_all([test_user1, test_user2, test_admin])
#         session.commit()


@basic_auth.verify_password
def verify_password(username, password):
    # print("verify")
    with Session() as session:
        # user = User.query.filter_by(username=username).first()
        # print(username, password)
        user = session.query(User).filter(User.nickname == username).first()
        # print(user)
        if user is None:
            return False
        g.current_user = user
        return user.check_password(password)


@basic_auth.login_required
def get_token():
    # print("get_token")
    with Session() as session:
        token = g.current_user.get_token(session)
        session.commit()
    return jsonify({'token': token})


@basic_auth.error_handler
def basic_auth_error():
    # return error_response(401)
    # print("basic_error")
    raise HTTPError(401, f"Access denied")


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


# убрать дублирование get?
def get_adv(adv_id: int, session: Session) -> Adv:
    adv = session.query(Adv).get(adv_id)
    if adv is None:
        raise HTTPError(400, f"adv_id {adv_id} not found ")
    return adv


def get_user(user_name: str, session: Session) -> User:
    user = session.query(User).filter(User.nickname == user_name).first()
    if user is None:
        raise HTTPError(400, f"user {user_name} not found ")
    return user


def get_user_by_token(token: str, session: Session) -> User:
    user = session.query(User).filter(User.token == token).first()
    if user is None:
        raise HTTPError(401, f"Token not found")
    # print(token, user.nickname)
    return user


def access_granted(owner: User, token: String, session: Session) -> Boolean:
    token_user = get_user_by_token(token, session)
    if token_user.is_admin == "true" or token_user == owner:
        return True
    raise HTTPError(401, f"Wrong token for user {owner.nickname}")


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
            token = request.headers["token"]
            print(user.nickname, token)
            if access_granted(user, token, session):
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


@app.route('/users/', methods=['POST'])
def new_user():
    with Session() as session:
        data = request.json
        password = data.pop("password")
        new_user = User(**data)
        new_user.set_password(password)
        session.add(new_user)
        session.commit()

        return jsonify({"status": "success", "hash": new_user.password_hash})


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
app.add_url_rule("/tokens/", methods=["POST"], view_func=get_token)

app.run(debug=True)

# if __name__ == "__main__":
#     with Session() as session:
#         test_user1 = User(nickname="TestUser1", email="a1@a.a", password_hash=generate_password_hash("1234"))
#         test_user2 = User(nickname="TestUsr2", email="a2@a.a", password_hash=generate_password_hash("5678"))
#         test_admin = User(nickname="TestAdmin", email="a3@a.a", password_hash=generate_password_hash("0007"), is_admin=True)
#         session.add_all([test_user1, test_user2, test_admin])
#         session.commit()
