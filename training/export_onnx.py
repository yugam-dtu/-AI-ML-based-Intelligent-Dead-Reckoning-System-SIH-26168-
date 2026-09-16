import torch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.tcn_velocity import TCNVelocityModel

model = TCNVelocityModel()
model.load_state_dict(torch.load('./outputs/velocity_model/best_velocity_model.pth', map_location='cpu'))
model.eval()

# Dummy input: (batch_size, time_steps, features) -> (1, 50, 9)
dummy_input = torch.randn(1, 50, 9)
torch.onnx.export(model, dummy_input, './outputs/velocity_model/velocity_model.onnx', 
                  export_params=True, opset_version=14, do_constant_folding=True, 
                  input_names=['input'], output_names=['output'],
                  dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}})
print("Exported to ONNX successfully!")
