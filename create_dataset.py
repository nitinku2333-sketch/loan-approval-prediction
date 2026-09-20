import pandas as pd
import random

random.seed(42)

data = []

for i in range(1000):

    gender = random.choice(["Male", "Female"])
    married = random.choice(["Yes", "No"])
    dependents = random.choice(["0", "1", "2", "3+"])
    education = random.choice(["Graduate", "Not Graduate"])
    self_employed = random.choice(["Yes", "No"])

    applicant_income = random.randint(1500, 15000)
    coapplicant_income = random.randint(0, 8000)

    loan_amount = random.randint(50, 500)
    loan_term = random.choice([120, 180, 240, 300, 360])

    credit_history = random.choice([0, 1])
    property_area = random.choice(["Urban", "Semiurban", "Rural"])

    if (
        credit_history == 1
        and applicant_income + coapplicant_income >= 4000
        and loan_amount <= 350
    ):
        loan_status = "Approved"
    else:
        loan_status = "Rejected"

    data.append([
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
        loan_status
    ])


columns = [
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
    "Property_Area",
    "Loan_Status"
]

df = pd.DataFrame(data, columns=columns)

df.to_csv("loan_data.csv", index=False)

print("Dataset created successfully!")
print("Total records:", len(df))