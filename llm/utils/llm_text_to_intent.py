from openai import OpenAI
from llamaapi import LlamaAPI
from dotenv import load_dotenv
import os

def load_api_key(api_name):
    try:
        load_dotenv()
        return os.getenv(f"{api_name}_KEY")
    except Exception as e:
        raise Exception(f"Error loading API key: {str(e)}")

def call_api(api, content, model):
    try:
        api_request_json = {
            "model": model,
            "messages": [
                {"role": "user", "content": content},
            ]
        }
        response = api.run(api_request_json)
        response_data = response.json()
        return response_data
    except Exception as e:
        raise Exception(f"Error calling API: {str(e)}")

def extract_label(predicted_label, labels):
    try:
        for label in labels:
            if label in predicted_label:
                return label
        return 'unknown'
    except Exception as e:
        raise Exception(f"Error extracting label: {str(e)}")

def get_prediction_llama_mistral(api_key, content, labels, model):
    try:
        llama = LlamaAPI(api_key)
        response_data = call_api(llama, content, model)

        predicted_label = None
        for choice in response_data['choices']:
            if choice['message']['role'] == 'assistant':
                predicted_label = choice['message']['content']
                break

        return extract_label(predicted_label, labels)
    except Exception as e:
        raise Exception(f"Error processing Llama/Mistral prediction: {str(e)}")

def get_prediction_gpt(content, labels, model):
    try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}]
        )
        prediction = completion.choices[0].message.content.lower()
        return extract_label(prediction, labels)
    except Exception as e:
        raise Exception(f"Error processing GPT prediction: {str(e)}")

def get_prediction(text_data, selected_model):
    try:
        labels = [
            'data profiling', 'classification', 'correlation', 
            'anomaly detection', 'clustering', 'causal inference', 
            'association rules', 'regression', 'forecasting'
        ]
        content = f"Classes: {labels}\nText: {text_data}\n\nClassify the text into one of the above classes."

        if "llama" in selected_model or "mixtral" in selected_model or "mistral" in selected_model:
            api_key = load_api_key("LlamaAPI")
            prediction = get_prediction_llama_mistral(api_key, content, labels, model=selected_model)
        elif "gpt" in selected_model:
            prediction = get_prediction_gpt(content, labels, model=selected_model)
        else:
            raise ValueError("Invalid model selected")

        return prediction
    except Exception as e:
        raise Exception(f"Error getting prediction: {str(e)}")
