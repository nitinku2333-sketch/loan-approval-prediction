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

init_db()


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


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
# LOAN PREDICTION
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

        gender_encoded = gender_encoder.transform(
            [gender]
        )[0]

        married_encoded = married_encoder.transform(
            [married]
        )[0]

        dependents_encoded = dependents_encoder.transform(
            [dependents]
        )[0]

        education_encoded = education_encoder.transform(
            [education]
        )[0]

        self_employed_encoded = self_employed_encoder.transform(
            [self_employed]
        )[0]

        property_area_encoded = property_area_encoder.transform(
            [property_area]
        )[0]


        # ==========================================
        # CREATE INPUT DATA
        # ==========================================

        input_data = pd.DataFrame(
            [[
                gender_encoded,
                married_encoded,
                dependents_encoded,
                education_encoded,
                self_employed_encoded,
                applicant_income,
                coapplicant_income,
                loan_amount,
                loan_term,
                credit_history,
                property_area_encoded
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
        # POSSIBLE REJECTION FACTORS
        # ==========================================

        reasons = []


        if prediction_result == "Rejected":

            # Credit history
            if credit_history == 0:

                reasons.append(
                    "Credit history is not favorable."
                )


            # Income vs loan amount
            total_income = (
                applicant_income +
                coapplicant_income
            )

            if total_income > 0:

                income_loan_ratio = (
                    loan_amount / total_income
                )

                if income_loan_ratio > 0.40:

                    reasons.append(
                        "Loan amount is relatively high compared with total income."
                    )


            # Applicant income
            if applicant_income < 30000:

                reasons.append(
                    "Applicant income may be relatively low for the requested loan."
                )


            # Co-applicant income
            if (
                coapplicant_income == 0
                and applicant_income < 40000
            ):

                reasons.append(
                    "There is no co-applicant income and applicant income is relatively low."
                )


            # Education
            if education == "Not Graduate":

                reasons.append(
                    "Applicant is not a graduate."
                )


            # Self employed
            if self_employed == "Yes":

                reasons.append(
                    "Self-employed status may affect the assessment."
                )


            # Dependents
            if dependents == "3+":

                reasons.append(
                    "Higher number of dependents may affect affordability."
                )


            # If no specific factor was found
            if len(reasons) == 0:

                reasons.append(
                    "The applicant profile does not sufficiently match patterns learned by the machine learning model."
                )


        # ==========================================
        # RESULT PAGE
        # ==========================================

        return render_template(
            "result.html",
            result=prediction_result,
            reasons=reasons
        )


    return render_template("predict.html")


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ==========================================
# START APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0"
    )
