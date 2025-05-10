from flask import Flask, render_template, request
from groq import Groq
import json

app = Flask(__name__)

client = Groq(api_key='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')

@app.route('/', methods=['GET', 'POST'])
def index():
    colleges = []
    if request.method == 'POST':
        try:
            cutoff = float(request.form['cutoff'])
            field = request.form['field']
            community = request.form['community']

            # ...existing code...
            prompt = f"""Analyze colleges in Tamil Nadu for:
            - Cutoff marks: {cutoff}
            - Field: {field}
            - Community: {community}

            Return exactly 10 colleges in this JSON format (no additional text):
            [
                {{
                    "name": "College Name",
                    "location": "City, District",
                    "prev_cutoff": "185.5",
                    "expected_cutoff": "186.0",
                    "seats": "60",
                    "rating": "A",
                    "recruiters": "120",
                    "admission_chance": "75"
                }}
            ]

            Rules:
            - Return exactly 10 colleges sorted by admission chance
            - location should be city and district
            - prev_cutoff and expected_cutoff should be numbers with one decimal
            - seats should be a number
            - rating should be A++, A+, A, B++, B+, or B
            - recruiters should be number of companies visited for placement
            - admission_chance should be a number between 0-100
            - All values must be strings
            - Return only the JSON array, no other text"""


            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a JSON-only response generator. Return valid JSON arrays without any additional text or formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,  # Lower temperature for more consistent output
                max_tokens=1600
            )
            
            # Clean and parse response
            response_text = response.choices[0].message.content.strip()
            
            # Remove any markdown or extra formatting
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON and validate structure
            colleges = json.loads(response_text)
            
            # Validate each college has required fields
            required_fields = ["name", "location", "prev_cutoff", "expected_cutoff", "seats", "rating", "recruiters", "admission_chance"]
            for college in colleges:
                for field in required_fields:
                    if field not in college:
                        raise ValueError(f"Missing required field: {field}")
            
        except json.JSONDecodeError as e:
            print(f"JSON Error: {response_text}")  # For debugging
            colleges = [{
                "name": "Error: Invalid response format",
                "prev_cutoff": "-",
                "expected_cutoff": "-",
                "seats": "-",
                "rating": "-",
                "admission_chance": "0"
            }]
        except Exception as e:
            print(f"Error: {str(e)}")  # For debugging
            colleges = [{
                "name": f"Error: {str(e)}",
                "prev_cutoff": "-",
                "expected_cutoff": "-",
                "seats": "-",
                "rating": "-",
                "admission_chance": "0"
            }]

    return render_template('index.html', colleges=colleges)

if __name__ == '__main__':
    app.run(debug=True)