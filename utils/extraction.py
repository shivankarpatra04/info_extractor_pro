import re
import spacy
import pandas as pd
from collections import Counter
from docx import Document

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_emails(text: str):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)

def extract_phone_numbers(text: str):
    phone_pattern = r'\+?(\d{1,3})?[-.\s]?(\(?\d{3}\)?)[-.\s]?(\d{3})[-.\s]?(\d{4})'
    return ["".join(match) for match in re.findall(phone_pattern, text)]

def extract_company_names(text: str):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "ORG"]

def extract_names_advanced(text: str):
    doc = nlp(text)
    spacy_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    
    patterns = [
        r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', 
        r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b',
        r'\b[A-Z][a-z]+ van [A-Z][a-z]+\b', 
        r'\b[A-Z][a-z]+ [a-z]+ [A-Z][a-z]+\b',
    ]
    regex_names = [name for pattern in patterns for name in re.findall(pattern, text)]
    
    titles = ['Mr', 'Mrs', 'Ms', 'Miss', 'Dr', 'Prof', 'Sir', 'Lady', 'Lord']
    title_names = []
    for token in doc:
        if token.text in titles and token.i + 1 < len(doc):
            name_start = token.i + 1
            name_end = name_start + 1
            while name_end < len(doc) and doc[name_end].pos_ == "PROPN":
                name_end += 1
            title_names.append(' '.join([t.text for t in doc[name_start:name_end]]))
    
    all_names = spacy_names + regex_names + title_names
    name_counts = Counter(all_names)
    
    filtered_names = [
        name for name, count in name_counts.items()
        if len(name.split()) >= 2 and not any(char.isdigit() for char in name)
        and not any(word.lower() in ['inc', 'ltd', 'llc', 'corp', 'corporation'] for word in name.split())
    ]
    
    sorted_names = sorted(filtered_names, key=lambda x: (-name_counts[x], -len(x)))
    return sorted_names

def extract_information(text: str):
    emails = extract_emails(text)
    phone_numbers = extract_phone_numbers(text)
    companies = extract_company_names(text)
    persons = extract_names_advanced(text)
    return {
        "emails": emails,
        "phone_numbers": phone_numbers,
        "companies": companies,
        "persons": persons
    }

def process_document(content: str):
    info = extract_information(content)
    
    max_length = max(len(info['emails']),
                     len(info['phone_numbers']),
                     len(info['companies']),
                     len(info['persons']))
    
    emails = info['emails'] + [None] * (max_length - len(info['emails']))
    phone_numbers = info['phone_numbers'] + [None] * (max_length - len(info['phone_numbers']))
    companies = info['companies'] + [None] * (max_length - len(info['companies']))
    persons = info['persons'] + [None] * (max_length - len(info['persons']))
    
    df = pd.DataFrame({
        "Emails": emails,
        "Phone Numbers": phone_numbers,
        "Companies": companies,
        "Persons": persons
    })
    return df

def read_file_content(file_path):
    content = ""
    if file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    elif file_path.endswith('.docx'):
        doc = Document(file_path)
        content = "\n".join([para.text for para in doc.paragraphs])
    return content
