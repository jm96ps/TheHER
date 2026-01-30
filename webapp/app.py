from flask import Flask
from .routes import bp as main_bp


def create_app():
    # Use package templates and static folders so templates in this package are used
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.register_blueprint(main_bp)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
