from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
import json
import traceback
import sys

print("Starting the Flask application...")

app = Flask(__name__, static_url_path='')
CORS(app)

try:
    print("Configuring Gemini API...")
    GEMINI_API_KEY = "AIzaSyDFWFyBHW3B90HpjZpXi-KfuqUnGWu6Tco"  # Replace with your actual API key
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
    print("Gemini API configured successfully!")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    sys.exit(1)

def analyze_news(content):
    try:
        prompt = f"""You are an expert fact-checker and news analyst. Analyze the following news content for authenticity.
        
        Analyze using these key factors:
        1. Language Analysis:
           - Check for sensationalist language
           - Identify emotional manipulation
           - Look for grammatical/spelling errors
        2. Source Credibility:
           - Extract mentioned sources
           - Look for verifiable claims
           - Check for expert citations
        3. Content Analysis:
           - Identify potential bias
           - Check logical consistency
           - Look for missing context
        4. Red Flags:
           - Check for clickbait elements
           - Identify unsupported claims
           - Look for manipulated statistics
        
        News content: {content}
        
        Provide a detailed analysis in this JSON format:
        {{
            "is_fake": boolean,
            "confidence": number,
            "analysis": string,
            "key_indicators": [string],
            "source_check": {{
                "mentioned_sources": [string],
                "verifiable_claims": [string],
                "credibility_score": number
            }},
            "bias_analysis": {{
                "political_bias": string,
                "emotional_manipulation_score": number,
                "objectivity_score": number
            }},
            "recommendations": [string]
        }}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text
        
        try:
            cleaned_response = response_text.replace('```json', '').replace('```', '').strip()
            parsed_json = json.loads(cleaned_response)
            
            # Convert decimal scores to percentages
            def convert_to_percentage(value):
                if isinstance(value, (int, float)):
                    if value <= 1:  # If value is in decimal (0.8 means 80%)
                        return int(value * 100)
                    return int(value)
                return 0

            # Convert all scores to percentages
            parsed_json['confidence'] = convert_to_percentage(parsed_json.get('confidence', 0))
            parsed_json['source_check']['credibility_score'] = convert_to_percentage(
                parsed_json['source_check'].get('credibility_score', 0)
            )
            parsed_json['bias_analysis']['objectivity_score'] = convert_to_percentage(
                parsed_json['bias_analysis'].get('objectivity_score', 0)
            )
            parsed_json['bias_analysis']['emotional_manipulation_score'] = convert_to_percentage(
                parsed_json['bias_analysis'].get('emotional_manipulation_score', 0)
            )

            # Update is_fake based on the converted scores
            if not isinstance(parsed_json.get('is_fake'), bool):
                # Determine if fake based on scores
                parsed_json['is_fake'] = (
                    parsed_json['confidence'] < 50 or
                    parsed_json['source_check']['credibility_score'] < 40 or
                    parsed_json['bias_analysis']['objectivity_score'] < 40 or
                    parsed_json['bias_analysis']['emotional_manipulation_score'] > 70
                )

            return json.dumps(parsed_json)
        except json.JSONDecodeError:
            print(f"Invalid JSON response: {response_text}")
            return json.dumps({
                "is_fake": True,  # Default to fake for error cases
                "confidence": 0,
                "analysis": "Error processing the content. Please try again.",
                "key_indicators": ["Error in analysis"],
                "source_check": {
                    "mentioned_sources": [],
                    "verifiable_claims": [],
                    "credibility_score": 0
                },
                "bias_analysis": {
                    "political_bias": "Unknown",
                    "emotional_manipulation_score": 100,  # High manipulation score for error cases
                    "objectivity_score": 0
                },
                "recommendations": ["Please try again with different content"]
            })
            
    except Exception as e:
        print(f"Error in analyze_news: {str(e)}")
        print(traceback.format_exc())
        raise

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
            
        news_content = data.get('content', '')
        if not news_content:
            return jsonify({'error': 'No content provided'}), 400
        
        result = analyze_news(news_content)
        return jsonify({'result': result})
    
    except Exception as e:
        print(f"Error in /api/analyze: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    try:
        print("\nServer is starting...")
        print("Access the application at: http://localhost:5000")
        print("Press CTRL+C to stop the server")
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
