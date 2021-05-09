from chalice import Chalice

app = Chalice(app_name='sample-api')


@app.route('/hello', methods=["POST"])
def index():
    return {'hello': app.current_request.json_body['name']}