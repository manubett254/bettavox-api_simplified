from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.utils import extract_features
from app.model import load_assets
from app.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from app.database import get_db  # PostgreSQL connection function
import pandas as pd
import os
import json
import logging
import secrets
from datetime import datetime

routes = Blueprint("routes", __name__)
logger = logging.getLogger(__name__)

(
    GENDER_MODELS, SCALER_GENDER, FEATURE_LIST,
    MODEL_STEP1, SCALER_STEP1, LABEL_ENCODER_STEP1,
    MODEL_STEP2, SCALER_STEP2, LABEL_ENCODER_STEP2
) = load_assets()


def allowed_file(filename):
    return filename.lower().endswith(tuple(ALLOWED_EXTENSIONS))


@routes.route("/predict", methods=["POST"])
def predict():
    api_key = request.headers.get("X-API-KEY")
    if not api_key:
        return jsonify({"error": "Missing API key"}), 401

    logger.info(f"Received prediction request from API key: {api_key}")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, plan FROM users WHERE api_key = %s", (api_key,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        return jsonify({"error": "Invalid API key"}), 403

    user_id, plan = user
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT request_count FROM usage WHERE user_id=%s AND date=%s", (user_id, today))
    row = cursor.fetchone()

    if plan == "free":
        if row and row[0] >= 5:
            cursor.close()
            return jsonify({"error": "Free plan limit reached (5/day)"}), 429
        elif row:
            cursor.execute(
                "UPDATE usage SET request_count = request_count + 1 WHERE user_id=%s AND date=%s",
                (user_id, today)
            )
        else:
            cursor.execute(
                "INSERT INTO usage (user_id, date, request_count) VALUES (%s, %s, 1)",
                (user_id, today)
            )

    file = request.files.get("audio")
    if not file or not allowed_file(file.filename):
        cursor.close()
        return jsonify({"error": "No valid file uploaded"}), 400

    if not file.mimetype.startswith('audio/'):
        return jsonify({"error": "Invalid file type. Audio only."}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1]
    random_filename = secrets.token_hex(8) + ext
    filepath = os.path.join(UPLOAD_FOLDER, random_filename)
    file.save(filepath)

    features = extract_features(filepath)
    if features is None:
        cursor.close()
        return jsonify({"error": "Failed to extract features"}), 500

    features_df = pd.DataFrame([features], columns=FEATURE_LIST)
    features_scaled_gender = SCALER_GENDER.transform(features_df)

    best_model, best_pred, best_conf = None, None, 0
    for name, model in GENDER_MODELS.items():
        pred = model.predict(features_scaled_gender)[0]
        conf = model.predict_proba(features_scaled_gender)[0].max() * 100
        if conf > best_conf:
            best_model, best_pred, best_conf = name, pred, conf

    gender = "Female" if best_pred == 1 else "Male"
    features_df["gender"] = best_pred

    features_scaled_step1 = SCALER_STEP1.transform(features_df)
    step1_pred_encoded = MODEL_STEP1.predict(features_scaled_step1)[0]
    step1_pred = LABEL_ENCODER_STEP1.inverse_transform([step1_pred_encoded])[0]

    if step1_pred == "child":
        age_group = "child"
        age_confidence = MODEL_STEP1.predict_proba(features_scaled_step1)[0].max() * 100
    else:
        features_scaled_step2 = SCALER_STEP2.transform(features_df)
        step2_pred_encoded = MODEL_STEP2.predict(features_scaled_step2)[0]
        age_group = LABEL_ENCODER_STEP2.inverse_transform([step2_pred_encoded])[0]
        age_confidence = MODEL_STEP2.predict_proba(features_scaled_step2)[0].max() * 100

    cursor.execute("""
        INSERT INTO predictions (
            audio_file, predicted_gender, predicted_age_group,
            confidence_score, gender_confidence, age_confidence,
            is_correct, features
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        filename, gender, age_group,
        float(age_confidence), float(best_conf), float(age_confidence),
        -1, json.dumps([float(f) for f in features])
    ))

    prediction_id = cursor.lastrowid
    conn.commit()
    cursor.close()

    os.remove(filepath)

    return jsonify({
        "id": prediction_id,
        "gender": gender,
        "gender_confidence": best_conf,
        "age_group": age_group,
        "age_confidence": age_confidence
    })


@routes.route("/register", methods=["POST"])
def register_submit():
    email = request.form.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    api_key = secrets.token_hex(16)
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, api_key) VALUES (%s, %s)", (email, api_key))
        conn.commit()
        cursor.close()
        return jsonify({"message": "Account created", "api_key": api_key})
    except Exception as e:
        if "duplicate key" in str(e).lower():
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": str(e)}), 500

@routes.route("/predictions", methods=["GET"])
def view_predictions():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, audio_file, predicted_gender, predicted_age_group, confidence_score, timestamp FROM predictions ORDER BY id DESC LIMIT 20")
        rows = cursor.fetchall()
        cursor.close()
        return jsonify([
            {
                "id": r[0],
                "audio_file": r[1],
                "gender": r[2],
                "age_group": r[3],
                "confidence": r[4],
                "timestamp": r[5].isoformat()
            }
            for r in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
