import pandas as pd

import pickle

from sklearn.model_selection import train_test_split

from sklearn.preprocessing import LabelEncoder

from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import accuracy_score


# ==========================================
# LOAD DATASET
# ==========================================

df = pd.read_csv("loan_data.csv")

print("Dataset loaded successfully!")

print("Total records:", len(df))


# ==========================================
# CREATE ENCODERS
# ==========================================

gender_encoder = LabelEncoder()

married_encoder = LabelEncoder()

dependents_encoder = LabelEncoder()

education_encoder = LabelEncoder()

self_employed_encoder = LabelEncoder()

property_area_encoder = LabelEncoder()

loan_status_encoder = LabelEncoder()


# ==========================================
# ENCODE CATEGORICAL COLUMNS
# ==========================================

df["Gender"] = gender_encoder.fit_transform(
    df["Gender"]
)

df["Married"] = married_encoder.fit_transform(
    df["Married"]
)

df["Dependents"] = dependents_encoder.fit_transform(
    df["Dependents"]
)

df["Education"] = education_encoder.fit_transform(
    df["Education"]
)

df["Self_Employed"] = self_employed_encoder.fit_transform(
    df["Self_Employed"]
)

df["Property_Area"] = property_area_encoder.fit_transform(
    df["Property_Area"]
)

df["Loan_Status"] = loan_status_encoder.fit_transform(
    df["Loan_Status"]
)


# ==========================================
# SHOW ENCODING INFORMATION
# ==========================================

print()
print("Loan Status Mapping:")
print(loan_status_encoder.classes_)

print()
print("Gender Mapping:")
print(gender_encoder.classes_)

print()
print("Married Mapping:")
print(married_encoder.classes_)

print()
print("Dependents Mapping:")
print(dependents_encoder.classes_)

print()
print("Education Mapping:")
print(education_encoder.classes_)

print()
print("Self Employed Mapping:")
print(self_employed_encoder.classes_)

print()
print("Property Area Mapping:")
print(property_area_encoder.classes_)


# ==========================================
# CREATE FEATURES AND TARGET
# ==========================================

X = df.drop(
    "Loan_Status",
    axis=1
)

y = df["Loan_Status"]


# ==========================================
# SPLIT DATASET
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(

    X,

    y,

    test_size=0.20,

    random_state=42

)


# ==========================================
# CREATE RANDOM FOREST MODEL
# ==========================================

model = RandomForestClassifier(

    n_estimators=100,

    random_state=42

)


# ==========================================
# TRAIN MODEL
# ==========================================

model.fit(
    X_train,
    y_train
)

print()
print("Model trained successfully!")


# ==========================================
# TEST MODEL
# ==========================================

y_pred = model.predict(
    X_test
)


# ==========================================
# CALCULATE ACCURACY
# ==========================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print(
    "Model Accuracy:",
    accuracy * 100
)


# ==========================================
# SAVE MODEL + ENCODERS
# ==========================================

model_data = {

    "model": model,

    "gender_encoder": gender_encoder,

    "married_encoder": married_encoder,

    "dependents_encoder": dependents_encoder,

    "education_encoder": education_encoder,

    "self_employed_encoder": self_employed_encoder,

    "property_area_encoder": property_area_encoder,

    "loan_status_encoder": loan_status_encoder

}


# ==========================================
# CREATE model.pkl
# ==========================================

with open(
    "model.pkl",
    "wb"
) as file:

    pickle.dump(
        model_data,
        file
    )


print()
print("model.pkl created successfully!")
