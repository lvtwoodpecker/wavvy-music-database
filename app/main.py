# Entry point for any of the FastAPI services
# The main.py file can be used to run the FastAPI application

from . import create_app

app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
