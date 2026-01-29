#!/usr/bin/env python3
"""
ICS AI Model Training Script
Trains an Isolation Forest model on collected telemetry data for anomaly detection.

Usage: python3 train_model.py [--data /path/to/data.csv] [--output /path/to/model.pkl]

The script will:
1. Load telemetry data from security_logs.csv
2. Extract normal operation data for training
3. Train an Isolation Forest model
4. Save the model as a .pkl file for deployment
"""

import argparse
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os
from datetime import datetime

# Configuration
FEATURES = ['flow_rate', 'pressure', 'temperature', 'motor_current']
CONTAMINATION = 0.01  # Expect ~1% anomalies in production

def load_data(data_path):
    """Load and preprocess telemetry data"""
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Parse the data column
    try:
        df['parsed_data'] = df['data'].apply(lambda x: eval(x) if isinstance(x, str) else x)
        df['flow_rate'] = df['parsed_data'].apply(lambda x: x.get('flow_rate', 0))
        df['pressure'] = df['parsed_data'].apply(lambda x: x.get('pressure', 0))
        df['temperature'] = df['parsed_data'].apply(lambda x: x.get('temperature', 0))
        df['motor_current'] = df['parsed_data'].apply(lambda x: x.get('motor_current', 0))
    except Exception as e:
        print(f"Error parsing data: {e}")
        # Try alternative parsing
        df = pd.DataFrame(df['data'].apply(eval).tolist())
    
    return df

def prepare_training_data(df):
    """Prepare features for training"""
    print("Preparing training data...")
    
    # Extract features
    X = df[FEATURES].copy()
    
    # Handle missing values
    X = X.fillna(X.mean())
    
    # Remove obvious anomalies (is_anomaly = 1) for training
    # We only want to train on normal data
    if 'is_anomaly' in df.columns:
        normal_mask = df['is_anomaly'] == 0
        X_normal = X[normal_mask]
        print(f"Using {len(X_normal)} normal samples for training")
    else:
        X_normal = X
        print(f"Using {len(X_normal)} samples for training (no anomaly labels)")
    
    return X_normal

def train_model(X_train):
    """Train the Isolation Forest model"""
    print("Training Isolation Forest model...")
    
    # Initialize model
    model = IsolationForest(
        n_estimators=100,
        contamination=CONTAMINATION,
        max_samples='auto',
        random_state=42,
        n_jobs=-1
    )
    
    # Train
    model.fit(X_train)
    
    # Get training score
    train_scores = model.decision_function(X_train)
    print(f"Training score range: {train_scores.min():.4f} to {train_scores.max():.4f}")
    print(f"Mean training score: {train_scores.mean():.4f}")
    
    return model

def evaluate_model(model, X_test):
    """Evaluate model performance (if we have labels)"""
    print("\nEvaluating model...")
    
    # Predict
    predictions = model.predict(X_test)
    
    # If we have labels, compute metrics
    if 'is_anomaly' in X_test.columns:
        y_true = X_test['is_anomaly']
        print("\nClassification Report:")
        print(classification_report(y_true, predictions))
    
    return predictions

def save_model(model, output_path):
    """Save the trained model"""
    print(f"\nSaving model to {output_path}...")
    joblib.dump(model, output_path)
    print("Model saved successfully!")
    
    # Also save metadata
    metadata = {
        'features': FEATURES,
        'contamination': CONTAMINATION,
        'trained_at': datetime.now().isoformat(),
        'n_estimators': 100
    }
    metadata_path = output_path.replace('.pkl', '_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {metadata_path}")

def main():
    parser = argparse.ArgumentParser(description="Train ICS Anomaly Detection Model")
    parser.add_argument("--data", 
                        default="/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv",
                        help="Path to training data CSV")
    parser.add_argument("--output",
                        default="/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/isolation_forest_model.pkl",
                        help="Output path for trained model")
    parser.add_argument("--test-split", type=float, default=0.2,
                        help="Fraction of data for testing")
    
    args = parser.parse_args()
    
    # Check data file exists
    if not os.path.exists(args.data):
        print(f"Error: Data file not found: {args.data}")
        print("Please collect data first using the AI node in collect mode.")
        return 1
    
    # Load data
    df = load_data(args.data)
    print(f"Loaded {len(df)} total records")
    
    # Prepare training data
    X = prepare_training_data(df)
    
    # Split for evaluation (if enough data)
    if len(X) > 100:
        X_train, X_test = train_test_split(X, test_size=args.test_split, random_state=42)
    else:
        X_train = X
        X_test = X
    
    # Train model
    model = train_model(X_train)
    
    # Evaluate (if test set has labels)
    evaluate_model(model, X_test)
    
    # Save model
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    save_model(model, args.output)
    
    print("\n" + "="*60)
    print("Training complete!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Deploy the model to {args.output}")
    print(f"2. Update ics_ai_node.service to use monitor mode")
    print(f"3. Restart the AI node: sudo systemctl restart ics_ai_node")
    
    return 0

if __name__ == "__main__":
    exit(main())

