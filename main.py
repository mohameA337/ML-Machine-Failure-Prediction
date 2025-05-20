from fastapi import FastAPI
from pydantic import BaseModel
import torch
import torch.nn as nn
import numpy as np
import pickle
import os

with open(os.path.join("MACHINE_FAILURE","data", "scaler.pkl"), "rb") as f:
    scaler = pickle.load(f)

class myNN(nn.Module):
    def __init__(self, input_dim, hidden_dim, dropout):
        super(myNN, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)


input_dim = 9
hidden_dim = 71      
dropout = 0.43305797500170606       
model = myNN(input_dim, hidden_dim, dropout)

model_path = os.path.join("MACHINE_FAILURE","notebooks", "model_weights.pt")
model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
model.eval()

app = FastAPI(title="Machine Failure Prediction (PyTorch)")


class SensorData(BaseModel):
    footfall: float
    AQ: float
    USS: float
    CS: float
    VOC: float
    RP: float
    IP: float
    Temperature: float
    tempMode: float

@app.post("/predict/pytorch")
def predict(data: SensorData):
    try:
        # Step 1: Create arrays
        num_input = np.array([[
            data.footfall, data.AQ, data.USS, data.CS,
            data.VOC, data.RP, data.IP, data.Temperature
        ]])
        cat_input = np.array([[data.tempMode]])

        # Step 2: Scale numerical features
        num_scaled = scaler.transform(num_input)

        # Step 3: Concatenate scaled numerical + categorical
        full_input = np.concatenate([num_scaled, cat_input], axis=1)

        # Step 4: Convert to tensor
        input_tensor = torch.tensor(full_input, dtype=torch.float32)

        # Step 5: Inference
        with torch.no_grad():
            prob = model(input_tensor)
            pred = int((prob > 0.5).item())

        return {
            "model": "pytorch",
            "prediction": pred,
            "status": "failure risk" if pred == 1 else "normal"
        }

    except Exception as e:
        print("Inference error:", e)
        return {"error": str(e)}