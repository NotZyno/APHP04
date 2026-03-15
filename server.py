from flask import Flask, send_file, request, jsonify

# Nie zapomnieć o pyinstaller --onefile --windowed main.py
# oraz o zmianie LATEST_VERSION i VERSION w ctk.py przy każdej aktualizacji
LATEST_VERSION = "1.1.1"

def parse_version(v_string):
    return tuple(map(int, v_string.split('.')))

def main():
    app = Flask(__name__)
    
    @app.route("/", methods=["GET"])
    def index():
        try:
            print(request.args.get("version"))
            if request.args.get("version") is None:
                return send_file("./dist/main.exe", as_attachment=True) # Jeżeli nie podano wersji, pobierz aktualną wersję
            if parse_version(request.args.get("version")) < parse_version(LATEST_VERSION):
                return send_file("./dist/main.exe", as_attachment=True)
            return jsonify({"update": "Brak aktualizacji"})
        except FileNotFoundError:
            return (jsonify({"update": "Nie znaleziono pliku aktualizacji"}), 404)

    app.run("0.0.0.0", 5000)
main()