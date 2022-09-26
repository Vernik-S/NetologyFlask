from flask import Flask, jsonify, request

app = Flask("server")




def test():
    data = request.json
    headers = request.headers
    qs = request.args


    return jsonify({"Hello": "World", "json": data, "headers": dict(headers), "qs": dict(qs)})


app.add_url_rule("/test/", view_func=test)
app.run(debug=True)