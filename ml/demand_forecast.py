import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

# Sample data for demand forecasting
def create_sample_demand_data():
    # Day (0-30), demand (0-100)
    data = []
    for day in range(30):
        demand = 50 + 10 * np.sin(day / 3) + np.random.randint(-10, 10)
        data.append([day, demand])
    return pd.DataFrame(data, columns=['day', 'demand'])

def train_demand_model():
    df = create_sample_demand_data()
    X = df[['day']]
    y = df['demand']
    model = LinearRegression()
    model.fit(X, y)
    return model

model = train_demand_model()

def predict_demand(day):
    return model.predict([[day]])[0]