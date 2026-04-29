import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import numpy as np

# Sample data for training
def create_sample_traffic_data():
    # Time of day (0-23), day of week (0-6), traffic level (0-10)
    data = []
    for hour in range(24):
        for day in range(7):
            traffic = (hour // 6) * 2 + (day // 5) * 1 + np.random.randint(0, 3)
            data.append([hour, day, traffic])
    return pd.DataFrame(data, columns=['hour', 'day', 'traffic'])

def train_traffic_model():
    df = create_sample_traffic_data()
    X = df[['hour', 'day']]
    y = df['traffic']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = RandomForestRegressor(n_estimators=10)
    model.fit(X_train, y_train)
    return model

model = train_traffic_model()

def predict_traffic(hour, day=0):
    return model.predict([[hour, day]])[0]