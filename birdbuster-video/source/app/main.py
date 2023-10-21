from flask import Flask, render_template, request, redirect, url_for
import werkzeug
from pyzbar.pyzbar import decode
from PIL import Image, UnidentifiedImageError
import sqlite3

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024

ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "gif"}

# Connect to database
db_con = sqlite3.connect("database.db")
db_con.row_factory = sqlite3.Row
db_cur = db_con.cursor()

@app.route("/")
def index():
    error = request.args.get('error')

    if error is None:
        return render_template("index.html")

    if error == "0":
        return render_template("index.html", error="Error: File too large to upload")

    if error == "1":
        return render_template("index.html", error="Error: Incorrect file type")

    if error == "2":
        return render_template("index.html", error="Error: Couldn't read image file")

    if error == "3":
        return render_template("index.html", error="Error: An internal error occurred")

    if error == "4":
        return render_template("index.html", error="Error: That is not a valid barcode")

@app.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
def request_entity_too_large(e):
    return redirect(url_for('index', error="0"))

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        f = request.files["uploaded_file"]

        if not f:
            return redirect(url_for('index'))

        if not f.filename.split(".")[-1] in ALLOWED_EXTENSIONS:
            return redirect(url_for('index', error="1"))

        try:
            image = Image.open(f)
            result = decode(image)
        except UnidentifiedImageError:
            return redirect(url_for('index', error="2"))

        produce = []
        error = None

        if result:
            item_name = result[0].data.decode("utf-8")

            try:
                # Usar parâmetros preparados para evitar SQL injection
                db_cur.execute("SELECT * FROM Movies WHERE name COLLATE NOCASE = ?", (item_name,))
                query_result = db_cur.fetchall()

                for row in query_result:
                    produce.append(
                        {"name": row["name"], "price": "{0:.2f}".format(row["price"])}
                    )

                if not query_result:
                    error = "The barcode '" + item_name + "' returned no results"
            except sqlite3.Error as e:
                return redirect(url_for('index', error="3"))

        else:
            return redirect(url_for('index', error="4"))

        return render_template("index.html", produce=produce, error=error)

    return render_template("index.html", produce=None, error="")

if __name__ == "__main__":
    app.run()
