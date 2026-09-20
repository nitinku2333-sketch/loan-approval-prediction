from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pickle
import pandas as pd

from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "loan_prediction_secret_key"


# ==========================================
# LOAD MACHINE LEARNING MODEL
# ==========================================

with open("model.pkl", "rb") as file:
    model_data = pickle.load(file)

model = model_data["model"]

gender_encoder = model_data["gender_encoder"]
married_encoder = model_data["married_encoder"]
dependents_encoder = model_data["dependents_encoder"]
education_encoder = model_data["education_encoder"]
self_employed_encoder = model_data["self_employed_encoder"]
property_area_encoder = model_data["property_area_encoder"]
loan_status_encoder = model_data["loan_status_encoder"]


# ==========================================
# DATABASE
# ==========================================

def get_db():

    conn = sqlite3.connect("database.db")

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()

    conn.close()


# ==========================================
# INITIALIZE DATABASE
# ==========================================
# Important for Render / Gunicorn

init_db()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    if "user_id" in session:

        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ==========================================
# REGISTER
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            conn.commit()

            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return "Email already registered!"

    return render_template("register.html")


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        return "Invalid email or password!"

    return render_template("login.html")


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )


# ==========================================
# LOAN PREDICTION PAGE
# ==========================================

@app.route("/predict", methods=["GET", "POST"])
def predict():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if request.method == "POST":

        # ==========================================
        # GET FORM DATA
        # ==========================================

        gender = request.form["gender"]

        married = request.form["married"]

        dependents = request.form["dependents"]

        education = request.form["education"]

        self_employed = request.form["self_employed"]

        applicant_income = float(
            request.form["applicant_income"]
        )

        coapplicant_income = float(
            request.form["coapplicant_income"]
        )

        loan_amount = float(
            request.form["loan_amount"]
        )

        loan_term = int(
            request.form["loan_term"]
        )

        credit_history = int(
            request.form["credit_history"]
        )

        property_area = request.form["property_area"]


        # ==========================================
        # ENCODE CATEGORICAL DATA
        # ==========================================

        gender = gender_encoder.transform(
            [gender]
        )[0]

        married = married_encoder.transform(
            [married]
        )[0]

        dependents = dependents_encoder.transform(
            [dependents]
        )[0]

        education = education_encoder.transform(
            [education]
        )[0]

        self_employed = self_employed_encoder.transform(
            [self_employed]
        )[0]

        property_area = property_area_encoder.transform(
            [property_area]
        )[0]


        # ==========================================
        # CREATE INPUT DATA
        # ==========================================

        input_data = pd.DataFrame(
            [[
                gender,
                married,
                dependents,
                education,
                self_employed,
                applicant_income,
                coapplicant_income,
                loan_amount,
                loan_term,
                credit_history,
                property_area
            ]],

            columns=[
                "Gender",
                "Married",
                "Dependents",
                "Education",
                "Self_Employed",
                "ApplicantIncome",
                "CoapplicantIncome",
                "LoanAmount",
                "Loan_Amount_Term",
                "Credit_History",
                "Property_Area"
            ]
        )


        # ==========================================
        # PREDICTION
        # ==========================================

        prediction = model.predict(input_data)

        prediction_result = loan_status_encoder.inverse_transform(
            prediction
        )[0]


        # ==========================================
        # RESULT PAGE
        # ==========================================

        return render_template(
            "result.html",
            result=prediction_result
        )


    return render_template("predict.html")


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==========================================
# START APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0"
    )
