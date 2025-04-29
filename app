import csv
import re
from difflib import get_close_matches

# Load CSV Data
def load_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

# Load the CSV datasets
dining_data = load_csv("dining.csv")
courses_data = load_csv("courses.csv")
events_data = load_csv("events.csv")
study_spaces_data = load_csv("study_spaces.csv")
feedback_data = load_csv("feedback.csv")

# Helper Functions
def get_shortest_wait_time(meal):
    """Return the dining hall with the shortest wait time for a specific meal."""
    column = f"wait_time_{meal}"
    shortest = None
    shortest_name = None
    for row in dining_data:
        if row[column].isdigit():
            wait_time = int(row[column])
            if shortest is None or wait_time < shortest:
                shortest = wait_time
                shortest_name = row['name']
    return shortest_name if shortest_name else "No data available."

def get_longest_wait_time(meal):
    """Return the dining hall with the longest wait time for a specific meal."""
    column = f"wait_time_{meal}"
    longest = None
    longest_name = None
    for row in dining_data:
        if row[column].isdigit():
            wait_time = int(row[column])
            if longest is None or wait_time > longest:
                longest = wait_time
                longest_name = row['name']
    return longest_name if longest_name else "No data available."

def get_highest_occupancy_at_time(time):
    """Return the building with the highest occupancy at a specific time."""
    highest_occupancy = None
    highest_building = None
    for row in study_spaces_data:
        if row['avg_occupancy_weekday']:
            occupancy_list = list(map(int, row['avg_occupancy_weekday'].split(',')))
            opening_hour = int(row['hours'].split('-')[0].split(':')[0])
            specified_hour = int(time.split(':')[0])
            index = specified_hour - opening_hour
            if 0 <= index < len(occupancy_list):
                if highest_occupancy is None or occupancy_list[index] > highest_occupancy:
                    highest_occupancy = occupancy_list[index]
                    highest_building = row['building']
    return highest_building if highest_building else "No data available."

def get_professors_for_course(course_code):
    """Return the professor(s) teaching a specific course."""
    professors = set()
    for row in courses_data:
        if row['dept'] + row['number'] == course_code.upper():
            professors.update([prof.strip() for prof in row['professor'].split(";")])
    return ", ".join(professors) if professors else "No professor found."

def events_at(location, date):
    """Return events happening at a specific location on a specific date."""
    # Normalize the date format in the query
    query_date = re.sub(r'^0', '', date.split('/')[0]) + '/' + re.sub(r'^0', '', date.split('/')[1]) + '/' + date.split('/')[2]
    
    # Normalize the location to lowercase for case-insensitive comparison
    normalized_location = location.lower()
    
    # Match events based on normalized location and date
    results = [row['title'] for row in events_data if row['location'].lower() == normalized_location and row['date'] == query_date]
    return ", ".join(results) if results else "No events found."

# Pattern-Based Query Engine
def process_query(query):
    query = query.lower()

    # Generalize and normalize variations
    query = query.replace("shortest wait time", "wait time shortest").replace("longest wait time", "wait time longest")
    query = query.replace("dining hall", "cafeteria").replace("restaurant", "cafeteria")
    
    patterns = [
        # Dining hall wait time queries
        (r"which dining hall has the (shortest|longest) wait time for (breakfast|lunch|dinner)", 
         lambda m: get_shortest_wait_time(m.group(3)) if m.group(1) == "shortest" else get_longest_wait_time(m.group(3))),
        
        # Study space occupancy queries
        (r"which building has the highest occupancy at (\d{1,2}:\d{2})", lambda m: get_highest_occupancy_at_time(m.group(1))),
        
        # Professor queries
        (r"which professor teach course ([a-z]+[0-9]+)", lambda m: get_professors_for_course(m.group(1))),
        
        # Events queries
        (r"(?:what )?events?(?: do we have)? at (.+?) on (\d{1,2}/\d{1,2}/\d{4})", lambda m: events_at(m.group(1), m.group(2))),
    ]
    
    for pattern, handler in patterns:
        match = re.search(pattern, query)
        if match:
            return handler(match)
    
    return "Sorry, I couldn't understand your question."

# Chatbot Interface
def chatbot():
    print("🤖 Welcome to the Smart Campus Assistant!")
    print("Ask anything about dining, study spaces, events, courses, or feedback.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in ["exit", "quit"]:
            print("👋 Goodbye! Have a great day on campus.")
            break
        response = process_query(query)
        print(f"Assistant: {response}\n")

# Run Chatbot
if __name__ == "__main__":
    chatbot()