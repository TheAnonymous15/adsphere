#!/usr/bin/env python3
"""
Create placeholder Blood Detection CNN model
This is a simple untrained model that can be fine-tuned on blood/gore dataset
"""
import torch
import torch.nn as nn
from pathlib import Path


class BloodDetectorCNN(nn.Module):
    """Simple CNN for blood/gore detection - placeholder model"""
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 2)  # [no_blood, blood]
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


if __name__ == "__main__":
    # Create and save the model
    model = BloodDetectorCNN()
    model.eval()

    # Save to models directory
    models_dir = Path(__file__).parent / "moderation_service" / "models_weights"
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / "blood_cnn.pth"
    torch.save({
        'model_state_dict': model.state_dict(),
        'model_class': 'BloodDetectorCNN',
        'input_size': (3, 224, 224),
        'classes': ['no_blood', 'blood'],
        'note': 'Placeholder model - train on blood/gore dataset for production'
    }, model_path)

    print(f"✅ Created placeholder blood detection model: {model_path}")
    print(f"   Size: {model_path.stat().st_size / 1024:.1f} KB")
    print(f"   Note: This is a placeholder - fine-tune on actual dataset for production")

