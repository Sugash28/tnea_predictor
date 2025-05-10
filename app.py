from flask import Flask, render_template, request
from groq import Groq
import json

app = Flask(__name__)

client = Groq(api_key='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')

def validate_college_data(college):
    """Validate and clean individual college data"""
    required_fields = {
        "name": str,
        "location": str,
        "prev_cutoff": str,
        "expected_cutoff": str,
        "seats": str,
        "rating": str,
        "recruiters": str,
        "admission_chance": str
    }

    valid_ratings = {"A++", "A+", "A", "B++", "B+", "B"}

    # Ensure required fields are present
    for field, field_type in required_fields.items():
        if field not in college:
            raise ValueError(f"Missing field: {field}")
        college[field] = str(college[field])

    # Validate values
    if college["rating"] not in valid_ratings:
        raise ValueError(f"Invalid rating: {college['rating']}")

    try:
        float(college["prev_cutoff"])
        float(college["expected_cutoff"])
        int(college["seats"])
        int(college["recruiters"])
        admission = float(college["admission_chance"])
        if not 0 <= admission <= 100:
            raise ValueError("Admission chance must be between 0 and 100")
    except ValueError as e:
        raise ValueError(f"Invalid numeric value: {str(e)}")

    return college

@app.route('/', methods=['GET', 'POST'])
def index():
    colleges = []
    if request.method == 'POST':
        try:
            cutoff = float(request.form['cutoff'])
            field = request.form['field']
            community = request.form['community']

            prompt = f"""
Return a JSON array of exactly 10 colleges in Tamil Nadu that match the following:
- Cutoff marks: {cutoff}
- Field: {field}
- Community: {community}

Format:
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
- Return exactly 10 colleges sorted by admission_chance (high to low)
- All values must be strings
- rating must be one of: A++, A+, A, B++, B+, B
- Return only valid JSON. No markdown or explanation.
"""

            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only generator. Respond with clean JSON only, no markdown or extra characters."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1600
            )

            response_text = response.choices[0].message.content.strip()

            # Strip any code block markers
            if response_text.startswith("```"):
                response_text = response_text.strip("`")
                if response_text.lower().startswith("json"):
                    response_text = response_text[4:].strip()

            colleges_raw = json.loads(response_text)

            if not isinstance(colleges_raw, list) or len(colleges_raw) != 10:
                raise ValueError("Response must contain exactly 10 colleges")

            colleges = [validate_college_data(college) for college in colleges_raw]

        except json.JSONDecodeError:
            print(f"JSON Error: {response_text}")
            colleges = [{
                "name": "Error: Invalid JSON format",
                "location": "-",
                "prev_cutoff": "-",
                "expected_cutoff": "-",
                "seats": "-",
                "rating": "-",
                "recruiters": "-",
                "admission_chance": "0"
            }]
        except Exception as e:
            print(f"Error: {str(e)}")
            colleges = [{
                "name": f"Error: {str(e)}",
                "location": "-",
                "prev_cutoff": "-",
                "expected_cutoff": "-",
                "seats": "-",
                "rating": "-",
                "recruiters": "-",
                "admission_chance": "0"
            }]

    return render_template('index.html', colleges=colleges)

if __name__ == '__main__':
    app.run(debug=True)
