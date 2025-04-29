import streamlit as st
import csv
import re
from difflib import get_close_matches
from datetime import datetime

# Load CSV Data
@st.cache_data
def load_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

# Load datasets
dining_data = load_csv("dining.csv")
courses_data = load_csv("courses.csv")
events_data = load_csv("events.csv")
study_spaces_data = load_csv("study_spaces.csv")
feedback_data = load_csv("feedback.csv")
recreation_data = load_csv("recreation.csv")
services_data = load_csv("services.csv")

# Backend helper functions (shortened a bit for space)
def get_dining_hall_by_wait_time(meal, criteria):
    column = f"wait_time_{meal}"
    target_value = None
    target_name = None
    for row in dining_data:
        if row[column] and row[column].strip().isdigit():
            wait_time = int(row[column])
            if target_value is None or (criteria == "shortest" and wait_time < target_value) or (criteria == "longest" and wait_time > target_value):
                target_value = wait_time
                target_name = row['name']
    return target_name if target_name else "No data available."

def get_building_by_occupancy_at_time(time, criteria="highest"):
    target_occupancy = None
    target_building = None
    if ":" in time:
        specified_hour = int(time.split(':')[0])
    else:
        specified_hour = int(time.rstrip('APMapm'))
        if time.lower().endswith('pm') and specified_hour != 12:
            specified_hour += 12
    for row in study_spaces_data:
        if row['avg_occupancy_weekday']:
            occupancy_list = list(map(int, row['avg_occupancy_weekday'].split(',')))
            hours_range = row['hours'].split('-')
            opening_hour = int(hours_range[0].split(':')[0])
            closing_hour = int(hours_range[1].split(':')[0])
            if opening_hour <= specified_hour < closing_hour:
                index = specified_hour - opening_hour
                if 0 <= index < len(occupancy_list):
                    current_occupancy = occupancy_list[index]
                    if (target_occupancy is None or 
                        (criteria == "highest" and current_occupancy > target_occupancy) or 
                        (criteria == "lowest" and current_occupancy < target_occupancy)):
                        target_occupancy = current_occupancy
                        target_building = row['building']
    return target_building if target_building else "No data available."

def get_professors_for_course(course_code):
    professors = set()
    match = re.match(r'([A-Za-z]+)(\d+)', course_code)
    if match:
        dept, number = match.groups()
        course_code = f"{dept}{number}"
    for row in courses_data:
        if row['dept'] + row['number'] == course_code.upper():
            professors.update([prof.strip() for prof in row['professor'].split(";")])
    return ", ".join(professors) if professors else "No professor found."

def events_at(location, date):
    try:
        if re.match(r'\d{1,2}/\d{1,2}/\d{4}', date):
            parts = date.split('/')
            month = int(parts[0])
            day = int(parts[1])
            year = int(parts[2])
            normalized_date = f"{month}/{day}/{year}"
        else:
            dt = datetime.strptime(date, '%Y-%m-%d')
            normalized_date = f"{dt.month}/{dt.day}/{dt.year}"
    except ValueError:
        normalized_date = date
    best_location = None
    locations = [row['location'] for row in events_data]
    matches = get_close_matches(location, locations, n=1, cutoff=0.6)
    if matches:
        best_location = matches[0]
    else:
        for loc in locations:
            if loc.lower() == location.lower():
                best_location = loc
                break
    if not best_location:
        return "No events found."
    results = []
    for row in events_data:
        event_date = row['date']
        event_date_parts = event_date.split('/')
        event_date = f"{int(event_date_parts[0])}/{int(event_date_parts[1])}/{event_date_parts[2]}"
        normalized_date_parts = normalized_date.split('/')
        normalized_date_without_zeros = f"{int(normalized_date_parts[0])}/{int(normalized_date_parts[1])}/{normalized_date_parts[2]}"
        if row['location'] == best_location and (event_date == normalized_date or event_date == normalized_date_without_zeros):
            results.append(row['title'])
    return ", ".join(results) if results else "No events found."

def process_query(query):
    query = query.lower().strip()
    query = query.strip('"\'')
    patterns = [
        (r"which dining hall has the (shortest|longest) wait time for (breakfast|lunch|dinner)", lambda m: get_dining_hall_by_wait_time(m.group(2), m.group(1))),
        (r"which building has the (highest|lowest) occupancy at (\d{1,2}:\d{2}|\d{1,2}(?:am|pm))", lambda m: get_building_by_occupancy_at_time(m.group(2), m.group(1))),
        (r"which professor(?:s)? teach(?:es)? course ([a-z]+\s*\d+)", lambda m: get_professors_for_course(m.group(1).replace(' ', ''))),
        (r"(?:what )?events?(?: do we have)? at (.+?) on (\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{1,2}-\d{1,2})", lambda m: events_at(m.group(1), m.group(2))),
    ]
    for pattern, handler in patterns:
        match = re.search(pattern, query)
        if match:
            return handler(match)
    return "Sorry, I couldn't understand your question. Please try rephrasing it."

# Streamlit App
st.title("🎓 Smart Campus Assistant")
st.markdown("Ask anything about dining, study spaces, courses, professors, or events! 🤖")

user_query = st.text_input("Enter your question:")
submit = st.button("Get Answer")

if submit and user_query:
    with st.spinner("Thinking..."):
        response = process_query(user_query)
    st.success(response)
