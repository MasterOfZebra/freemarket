#!/usr/bin/env python3
"""
train.py - ML Training Pipeline for FreeMarket Matching
Trains a TF-IDF + LogisticRegression model to predict good matches
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
from datetime import datetime

def load_data(data_path):
    """Load training data from CSV"""
    print(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Expected columns: item_text, match_text, is_good_match, score
    required_cols = ['item_text', 'match_text', 'is_good_match']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data must contain columns: {required_cols}")

    # Combine texts for TF-IDF
    df['combined_text'] = df['item_text'] + ' ' + df['match_text']

    print(f"Loaded {len(df)} samples")
    return df

def create_pipeline():
    """Create sklearn pipeline with TF-IDF and LogisticRegression"""
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words='english',
            min_df=2
        )),
        ('classifier', LogisticRegression(
            random_state=42,
            max_iter=1000,
            C=1.0
        ))
    ])

def train_model(X, y):
    """Train the model"""
    print("Training model...")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Create and train pipeline
    pipeline = create_pipeline()
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]

    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    print(".3f")

    return pipeline

def save_model(pipeline, output_path):
    """Save trained model"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(pipeline, output_path)
    print(f"Model saved to {output_path}")

    # Also save metadata
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'model_type': 'tfidf_logistic_regression',
        'vectorizer_config': pipeline.named_steps['tfidf'].get_params(),
        'classifier_config': pipeline.named_steps['classifier'].get_params()
    }

    metadata_path = output_path.replace('.pkl', '_metadata.json')
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata saved to {metadata_path}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python train.py <data.csv> <output_model.pkl>")
        sys.exit(1)

    data_path = sys.argv[1]
    output_path = sys.argv[2]

    # Load data
    df = load_data(data_path)

    # Prepare features and target
    X = df['combined_text']
    y = df['is_good_match']

    # Train model
    model = train_model(X, y)

    # Save model
    save_model(model, output_path)

    print("Training completed successfully!")

if __name__ == '__main__':
    main()
