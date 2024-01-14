import nltk
from nltk import pos_tag
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import re
import spacy
from flask import Flask, request, render_template, jsonify
import traceback

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

app = Flask(__name__)
ans = []
#preprocessing text removinf stop wrods, punctuation marks, adjectives, can do lemmatising but not necessary here
def ExtractPII(text):
    try:
        ans.clear()
        def remove_stopwords(text):
            words = word_tokenize(text)
            stop_words = set(stopwords.words('english'))
            stop_words_set = set(stop_words)
            stop_words.update(stop_words_set)
            filtered_words = [word for word in words if word.lower() not in stop_words]
            filtered_text = ' '.join(filtered_words)
            return filtered_text

        def remove_adverbs(text):
            words = word_tokenize(text)
            pos_tags = pos_tag(words)

            def is_adverb(tag):
                return tag[1].startswith('RB')

            filtered_words = [word for word, tag in zip(words, pos_tags) if not is_adverb(tag)]
            filtered_text = ' '.join(filtered_words)
            return filtered_text

        def remove_punctuation(text):
            translator = str.maketrans("", "", string.punctuation)
            return text.translate(translator)

        text_without_stopwords = remove_stopwords(text)
        text_without_adverbs = remove_adverbs(text_without_stopwords)
        cleaned_text = remove_punctuation(text_without_adverbs)

        nlp = spacy.load("en_core_web_sm")


        doc = nlp(cleaned_text)

        merged_entities = []
        current_entity = None

        for ent in doc.ents:
            if current_entity is None or ent.label_ == current_entity["label"]:
                if current_entity is None:
                    current_entity = {"start": ent.start_char, "end": ent.end_char, "label": ent.label_, "text": ent.text}
                else:
                    current_entity["end"] = ent.end_char
                    current_entity["text"] += " " + ent.text
            else:
                merged_entities.append(current_entity)
                current_entity = {"start": ent.start_char, "end": ent.end_char, "label": ent.label_, "text": ent.text}

        if current_entity is not None:
            merged_entities.append(current_entity)

        excluded_terms = ["voter", "employee", "candidate", "participant", "user", "customer", "resident", "individual",
                          "citizen"]

        for entity in merged_entities:
            if entity['label'] == "PERSON" or entity['label'] == "GPE":
                if entity['label'] == "PERSON":
                    entity['label'] = "Name"
                if entity['label'] == "GPE":
                    entity['label'] = "ADDRESS"

                entity['text'] = entity['text'].lower()
                if entity['text'] not in excluded_terms:
                    ans.append({entity['label']: entity['text']})

        aadhaar_pattern = re.compile(r'\b\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b')
        aadhaar_numbers = aadhaar_pattern.findall(cleaned_text)
        passport_pattern = re.compile(r'\b[A-Z]{3}\d+\b')
        passport_numbers = passport_pattern.findall(cleaned_text)
        mobile_pattern = re.compile(r'\b\d{10}\b')
        mobile_numbers = mobile_pattern.findall(cleaned_text)
        ans.append({"Adhaar number": aadhaar_numbers})
        ans.append({"Phone number": mobile_numbers})
        ans.append({"Passport number": passport_numbers})
        ans.append({"error ":"NULL"})
        return ans

    except Exception as e:
        # Log the error to error_log.txt
        with open('error_log.txt', 'a') as f:
            f.write(f"Error: {str(e)}\n")
            traceback.print_exc(file=f)
#logging into file and displaying it
        ans.append({"error": str(e)})
        return ans

#lets assume inout is like this , the error is logged into the file and is displayed also
'''anss=ExtractPII(1234)
for i in anss:
    print("output is :",i)'''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze-pii', methods=['POST'])
def analyze_pii():
    if request.method == 'POST':
        data = request.get_json()
        text = data.get('text', '')
        result = ExtractPII(text)
        return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
