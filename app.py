from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pickle
import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# FLASK APPLICATION
# ==========================================

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


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def init_db():

    conn = get_db()

    # --------------------------------------
    # USERS TABLE
    # --------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)


    # --------------------------------------
    # PREDICTIONS TABLE
    # --------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,

            gender TEXT NOT NULL,
            married TEXT NOT NULL,
            dependents TEXT NOT NULL,
            education TEXT NOT NULL,
            self_employed TEXT NOT NULL,

            applicant_income REAL NOT NULL,
            coapplicant_income REAL NOT NULL,
            loan_amount REAL NOT NULL,
            loan_term INTEGER NOT NULL,
            credit_history INTEGER NOT NULL,
            property_area TEXT NOT NULL,

            result TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()

    conn.close()


# Initialize database when application starts
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


        # Hash password
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
# FORGOT PASSWORD
# ==========================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"].strip()

        new_password = request.form["new_password"]

        confirm_password = request.form["confirm_password"]


        # --------------------------------------
        # CHECK EMPTY FIELDS
        # --------------------------------------

        if not email or not new_password or not confirm_password:

            return "All fields are required!"


        # --------------------------------------
        # CHECK PASSWORD MATCH
        # --------------------------------------

        if new_password != confirm_password:

            return "New password and confirm password do not match!"


        # --------------------------------------
        # CHECK PASSWORD LENGTH
        # --------------------------------------

        if len(new_password) < 6:

            return "Password must contain at least 6 characters!"


        # --------------------------------------
        # FIND USER
        # --------------------------------------

        conn = get_db()

        user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()


        if not user:

            conn.close()

            return "No account found with this email!"


        # --------------------------------------
        # HASH NEW PASSWORD
        # --------------------------------------

        hashed_password = generate_password_hash(
            new_password
        )


        # --------------------------------------
        # UPDATE PASSWORD
        # --------------------------------------

        conn.execute(
            """
            UPDATE users
            SET password = ?
            WHERE id = ?
            """,
            (
                hashed_password,
                user["id"]
            )
        )

        conn.commit()

        conn.close()


        # --------------------------------------
        # GO BACK TO LOGIN
        # --------------------------------------

        return redirect(url_for("login"))


    return render_template("forgot_password.html")


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))


    user_id = session["user_id"]

    conn = get_db()


    # --------------------------------------
    # TOTAL PREDICTIONS
    # --------------------------------------

    total_predictions = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM predictions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()["total"]


    # --------------------------------------
    # APPROVED PREDICTIONS
    # --------------------------------------

    approved_predictions = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM predictions
        WHERE user_id = ?
        AND result = 'Approved'
        """,
        (user_id,)
    ).fetchone()["total"]


    # --------------------------------------
    # REJECTED PREDICTIONS
    # --------------------------------------

    rejected_predictions = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM predictions
        WHERE user_id = ?
        AND result = 'Rejected'
        """,
        (user_id,)
    ).fetchone()["total"]


    # --------------------------------------
    # RECENT PREDICTIONS
    # --------------------------------------

    recent_predictions = conn.execute(
        """
        SELECT *
        FROM predictions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user_id,)
    ).fetchall()


    conn.close()


    return render_template(
        "dashboard.html",
        name=session["user_name"],
        total_predictions=total_predictions,
        approved_predictions=approved_predictions,
        rejected_predictions=rejected_predictions,
        recent_predictions=recent_predictions
    )


# ==========================================
# USER PROFILE
# ==========================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    # --------------------------------------
    # CHECK LOGIN
    # --------------------------------------

    if "user_id" not in session:

        return redirect(url_for("login"))


    user_id = session["user_id"]

    conn = get_db()


    # --------------------------------------
    # GET CURRENT USER
    # --------------------------------------

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()


    # --------------------------------------
    # POST REQUEST
    # --------------------------------------

    if request.method == "POST":

        action = request.form.get("action")


        # ======================================
        # UPDATE NAME
        # ======================================

        if action == "update_name":

            name = request.form["name"].strip()


            if not name:

                conn.close()

                return "Name cannot be empty!"


            conn.execute(
                """
                UPDATE users
                SET name = ?
                WHERE id = ?
                """,
                (
                    name,
                    user_id
                )
            )


            conn.commit()


            # Update session name
            session["user_name"] = name


            conn.close()


            return redirect(url_for("profile"))


        # ======================================
        # CHANGE PASSWORD
        # ======================================

        if action == "change_password":

            current_password = request.form["current_password"]

            new_password = request.form["new_password"]

            confirm_password = request.form["confirm_password"]


            # ----------------------------------
            # CHECK CURRENT PASSWORD
            # ----------------------------------

            if not check_password_hash(
                user["password"],
                current_password
            ):

                conn.close()

                return "Current password is incorrect!"


            # ----------------------------------
            # CHECK PASSWORD LENGTH
            # ----------------------------------

            if len(new_password) < 6:

                conn.close()

                return "New password must contain at least 6 characters!"


            # ----------------------------------
            # CHECK PASSWORD MATCH
            # ----------------------------------

            if new_password != confirm_password:

                conn.close()

                return "New password and confirm password do not match!"


            # ----------------------------------
            # HASH NEW PASSWORD
            # ----------------------------------

            hashed_password = generate_password_hash(
                new_password
            )


            # ----------------------------------
            # UPDATE PASSWORD
            # ----------------------------------

            conn.execute(
                """
                UPDATE users
                SET password = ?
                WHERE id = ?
                """,
                (
                    hashed_password,
                    user_id
                )
            )


            conn.commit()

            conn.close()


            return redirect(url_for("profile"))


    # --------------------------------------
    # CLOSE DATABASE
    # --------------------------------------

    conn.close()


    # --------------------------------------
    # PROFILE PAGE
    # --------------------------------------

    return render_template(
        "profile.html",
        user=user
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


            # --------------------------------------
            # CREDIT HISTORY
            # --------------------------------------

            if credit_history == 0:

                reasons.append(
                    "Credit history is not favorable."
                )


            # --------------------------------------
            # INCOME VS LOAN AMOUNT
            # --------------------------------------

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


            # --------------------------------------
            # APPLICANT INCOME
            # --------------------------------------

            if applicant_income < 30000:

                reasons.append(
                    "Applicant income may be relatively low for the requested loan."
                )


            # --------------------------------------
            # CO-APPLICANT INCOME
            # --------------------------------------

            if (
                coapplicant_income == 0
                and applicant_income < 40000
            ):

                reasons.append(
                    "There is no co-applicant income and applicant income is relatively low."
                )


            # --------------------------------------
            # EDUCATION
            # --------------------------------------

            if education == "Not Graduate":

                reasons.append(
                    "Applicant is not a graduate."
                )


            # --------------------------------------
            # SELF EMPLOYED
            # --------------------------------------

            if self_employed == "Yes":

                reasons.append(
                    "Self-employed status may affect the assessment."
                )


            # --------------------------------------
            # DEPENDENTS
            # --------------------------------------

            if dependents == "3+":

                reasons.append(
                    "Higher number of dependents may affect affordability."
                )


            # --------------------------------------
            # DEFAULT REASON
            # --------------------------------------

            if len(reasons) == 0:

                reasons.append(
                    "The applicant profile does not sufficiently match patterns learned by the machine learning model."
                )


        # ==========================================
        # SAVE PREDICTION TO DATABASE
        # ==========================================

        conn = get_db()


        conn.execute(
            """
            INSERT INTO predictions (

                user_id,

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
                property_area,

                result,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,

            (
                session["user_id"],

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
                property_area,

                prediction_result,

                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )


        conn.commit()

        conn.close()


        # ==========================================
        # RESULT PAGE
        # ==========================================

        return render_template(
            "result.html",
            result=prediction_result,
            reasons=reasons
        )


    # ==========================================
    # PREDICTION PAGE
    # ==========================================

    return render_template("predict.html")


# ==========================================
# PREDICTION HISTORY
# ==========================================

@app.route("/history")
def history():

    if "user_id" not in session:

        return redirect(url_for("login"))


    user_id = session["user_id"]

    conn = get_db()


    predictions = conn.execute(
        """
        SELECT *
        FROM predictions
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()


    conn.close()


    return render_template(
        "history.html",
        predictions=predictions
    )


# ==========================================
# DELETE SINGLE PREDICTION
# ==========================================

@app.route("/history/delete/<int:prediction_id>")
def delete_prediction(prediction_id):

    if "user_id" not in session:

        return redirect(url_for("login"))


    conn = get_db()


    conn.execute(
        """
        DELETE FROM predictions
        WHERE id = ?
        AND user_id = ?
        """,
        (
            prediction_id,
            session["user_id"]
        )
    )


    conn.commit()

    conn.close()


    return redirect(url_for("history"))


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
