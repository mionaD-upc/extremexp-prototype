from flask import Flask, request, jsonify
from llm_text_to_intent import get_prediction

app = Flask(__name__)

MODEL = "mistral-7b-instruct"  # Specify the model you want to use

routes_info = {
        "/predictIntent": {
            "method": "POST",
            "description": "Classify text and return the intent.",
            "request_body": {
                "text": "string"
            },
            "response": {
                "intent": "string"
            },
            "example_usage": {
                "curl": 'curl -X POST http://localhost:8001/captureIntent/predict -H "Content-Type: application/json" -d \'{"text": "Your text to classify"}\''
            }
        }
    } 

@app.route('/', methods=['GET'])
def base_route():
    return jsonify(routes_info), 200

@app.route('/predictIntent', methods=['POST'])
def predict():
    """
    Endpoint to classify text.

    Request body should contain:
    {
        "text": "Your text to classify"
    }
    """
    try:
        data = request.json
        text = data.get("text")

        if not text:
            return jsonify({"error": "Text parameter is required."}), 400

        # Get prediction using the fixed provider and model
        prediction = get_prediction(text, f"{MODEL}")
        
        return jsonify({"intent": prediction, "model":f"{MODEL}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8001)
