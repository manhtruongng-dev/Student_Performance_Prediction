import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.model_selection import train_test_split
def clean(df):
    df = df.copy()
    df["absences"] = df["absences"].clip(upper=20)
    return df
def add_engineer(df):
    df = df.copy()
    df["study_per_absence"] = df["studytime"] / (df["absences"] + 1)
    df["failure_impact"] = df["failures"] * df["absences"]
    # df['total_edu']=df['Medu']+df['Fedu']
    # df['total_alc'] = df['Dalc']+df['Walc']
    # df['G2_adjusted'] = df['G2']*(1-df['absences']/100)
    return df

def build_preprocessor():
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="mean")),
        ("scaler", StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer([
        ("num", num_pipeline, make_column_selector(dtype_include=["number"])),
        ("cat", cat_pipeline, make_column_selector(dtype_include=["object", "string", "category", "bool"]))
    ])

    return preprocessor

def load_and_split(path):
    df_raw = pd.read_csv(path, sep=";") 

    df_clean = add_engineer(clean(df_raw))
    selected_features = [
        'G1', 'G2', 'failures', 'age', 'traveltime', 'goout', 'studytime', 'Medu', 'Fedu',
        'study_per_absence', 'failure_impact'
        # 'total_edu','total_alc'
        # 'G2_adjusted'
    ]

    X = df_clean[selected_features]
    y = df_clean["G3"]
    return train_test_split(X, y, test_size=0.2, random_state=42)