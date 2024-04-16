import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import pycountry

def get_wikipedia_html(person_name):
    """Fetch the full HTML of a person's Wikipedia page."""
    URL = "https://en.wikipedia.org/wiki/" + person_name.replace(" ", "_")
    try:
        response = requests.get(URL)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""

def test_wikipedia_page_existence(person_name):
    """Test if a Wikipedia page exists for the given person."""
    URL = "https://en.wikipedia.org/wiki/" + person_name.replace(" ", "_")
    response = requests.get(URL)
    if response.status_code != 200:
        print(f"Wikipedia page for {person_name} does not exist.")
    else:
        return

def extract_first_paragraph(html_content):
    """
    Fetches and extracts the first paragraph of a Wikipedia article from its HTML content.
    
    Returns:
    str: The text of the first paragraph, or an error message if not found.
    """
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the first paragraph in the main content area
    # Wikipedia's main content usually resides within <div id="content">
    content_div = soup.find('div', id='content')
    print(content_div)
    first_paragraph = content_div.find('p')

    if first_paragraph:
        return first_paragraph.get_text()
    else:
        return "No paragraph found."

def find_all_countries_in_text(text):
    """
    Searches the provided text for all unique country names using the pycountry library and additional mappings.
    
    Args:
        text (str): The text to search within.
    
    Returns:
        list: A list of all unique countries found, or an empty list if no countries are found.
    """
    # Normalize text for case-insensitive comparison
    text = text.lower()

    # Set to store unique country names found
    countries_found = set()

    # Check for direct country names using pycountry
    for country in pycountry.countries:
        if country.name.lower() in text:
            countries_found.add(country.name)

    # Additional mapping for constituent countries and regions
    constituent_to_country = {
        "u.s.": "United States",
        "england": "United Kingdom",
        "scotland": "United Kingdom",
        "wales": "United Kingdom",
        "northern ireland": "United Kingdom",
        "puerto rico": "United States",
        "hong kong": "China",
        # Add more as necessary
    }

    # Check for mapped regions or constituent countries
    for region, country in constituent_to_country.items():
        if region in text:
            countries_found.add(country)

    return list(countries_found)

def extract_summary(html_content):
    """Extract the summary from the Wikipedia infobox within the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    infobox = soup.find('table', class_='infobox')
    return infobox.get_text() if infobox else "Unknown"

def extract_birth_year(html_content):
    """Extract the birth year from the Wikipedia infobox within the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    infobox = soup.find('table', class_='infobox')
    if infobox:
        birth_date_text = infobox.find('span', class_='bday')
        if birth_date_text:
            birth_year = re.search(r'\d{4}', birth_date_text.text)
            return birth_year.group() if birth_year else "Unknown"
    return "Unknown"

def extract_country_of_origin(html_content):
    """Extract the country of origin from the Wikipedia infobox within the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    infobox = soup.find('table',  class_=['infobox', 'infobox-full-data'])

    # Return the HTML content of the infobox if found, otherwise indicate

    # METHOD 1 - Use the Infobox to find birth location
    if infobox:
        # Attempt to find the "Born" row in the infobox
        for row in infobox.find_all('tr'):
            print(row)
            th = row.find('th')
            if th and 'born' in th.text.lower():
                td = row.find('td')
                if td:
                    print(td.text)
                    # # [US Hardcode] Use regex to extract the country name
                    # us_search = re.search(r'U.S.|United States', td.text)
                    # if us_search:
                    #     return "United States"

                    # Find all country names and pick the first one
                    other_countries_in_text = find_all_countries_in_text(td.text)
                    if len(other_countries_in_text) > 0:
                        return other_countries_in_text[0]

                    # Last resort
                    # This is a basic regex that matches common country patterns and needs to be customized based on expected inputs
                    country_search = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', td.text)
                    if country_search:
                        return country_search.group(0)
    return "Unknown"

def extract_job(html_content):
    """Categorize the person based on job-related keywords with enhanced handling to differentiate between 'Politician' and 'Head of State'."""
    text = html_content.lower()

    # Define categories and their associated keywords
    categories = {
        "Government": ["politician", "diplomat", "senator", "governor", "mayor", "congressman", " mp ", "councillor", "secretary", "treasur", "democrat", "republic", "president", "prime minister", "chancellor", "king", "queen", "emperor", "sultan", "shah", "monarch"],
        "Scientist": ["scientist", "physicist", "chemist", "biologist", "researcher", "hypothesis", "doctor", "inventor", "engineer"],
        "Author": ["author", "writer", "novelist", "playwright", "poet", "bard"],
        "Artist": ["artist", "singer", "musician", "actor", "painter", "director", "dancer", "actress"],
        "Business Leader": ["business", "entrepreneur", "executive", "founder", "ceo", "industrialist"],
        "Athlete": ["athlete", "sports", "football", "basketball", "runner", "swimmer", "tennis", "baseball", "volleyball", "track and field", "hockey"],
        "Religious": ["priest", "pope", "rabbi", "imam", "bible", "reverend", "minister"]
    }

    # Function to calculate keyword frequency
    def calculate_keyword_frequency(keywords):
        return sum(text.count(keyword) for keyword in keywords)

    # Calculate scores for non-political categories
    category_scores = {category: calculate_keyword_frequency(keywords) for category, keywords in categories.items()}

    # Determine the primary category from non-political ones
    primary_category = max(category_scores, key=category_scores.get, default=None) if category_scores else None

    return primary_category if primary_category and category_scores.get(primary_category, 0) > 0 else "Unknown"


def main():
    # Load your dataset
    file_path = 'Trivia Draft - Wikipedia_Full_20240414.tsv'  # Change this to the path of your actual file
    print(file_path)
    df = pd.read_csv(file_path, sep='\t')
    #df = df.head(5)
    
    # print("Step 0: Running Tests")
    # df['Candidate'].apply(test_wikipedia_page_existence)
    
    print("Step 1: Retrieve Wikipedia Context")
    df['HTML Content'] = df['Candidate'].apply(get_wikipedia_html)
    print("Step 2: Parse Key Fields")
    df['Summary'] = df['HTML Content'].apply(extract_summary)  # Extract summary for categorization
    df['Birth Year'] = df['HTML Content'].apply(extract_birth_year)
    df['Country of Origin'] = df['HTML Content'].apply(extract_country_of_origin)
    df['Job'] = df['HTML Content'].apply(extract_job)
    
    # Save the updated DataFrame
    df.drop(columns=['HTML Content'], inplace=True)
    df.drop(columns=['Summary'], inplace=True)
    
    print("Step 3: Save New File")
    print(df)
    df.to_csv('updated_dataset.tsv', sep='\t', index=False)

if __name__ == "__main__":
    main()
    
##### Roadmap
# - some names in initial sheet are wrong and do not map properly to wikipedia --> build a test for this (Pretty Solid)
# - need to check accuracy of job algo (Pretty Solid)
# - need to check accuracy of country algo (Incomplete - lots of issues)
# - need to check accuracy of birth year algo (Pretty Solid - issues with Circa)
# - can we automate the extraction of inbound links count from the third party site (not started)
# - analytics/model for predicting the score (not started)
