from flask import Flask, render_template, request
import os
from parser import FlightScheduleParser

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    output_text = ""

    if request.method == "POST":
        file = request.files["csv_file"]
        if file:
            filepath = "uploaded.csv"
            file.save(filepath)

            parser = FlightScheduleParser(filepath)
            parser.load_csv()
            parser.find_date_header_row()
            parser.find_flight_data_start()
            parser.extract_date_headers()
            parser.extract_flights()
            output_text = parser.get_final_output()

            os.remove(filepath)

    return render_template("index.html", output=output_text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
