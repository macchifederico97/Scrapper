from flask import Flask
from routes import api_blueprint   # Importing the api routes
from WSManageLogin import visualfabriq_login
from ConfigParser import parse_config

def create_app():
    app = Flask(__name__)

    # Base configuration
    app.config["DEBUG"] = True

    # Registering "api" routes
    app.register_blueprint(api_blueprint, url_prefix="/api")

    return app

if __name__ == "__main__":
    app = create_app()
    organisationId, mail, password = parse_config("config.ini")
    print("Login Status: " + str(visualfabriq_login(organisationId, mail, password)))
    app.run(debug=False)
