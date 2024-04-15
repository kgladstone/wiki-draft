import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

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
    """Extract the country of origin from the provided Wikipedia text."""
    # Search for patterns indicating the country of origin
    patterns = [
        r"born in\s*([^,.]+)",
        r"from\s*([^,.]+)",
        r"originally from\s*([^,.]+)",
        r"raised in\s*([^,.]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            # Get the matched group
            country = match.group(1).strip()
            # Check if it's a link, and if so, extract the country from the linked page
            if "<a" in country:
                soup = BeautifulSoup(country, "html.parser")
                link = soup.find("a")
                # Follow the link and extract the country from the linked page
                if link and link.get("href"):
                    linked_url = "https://en.wikipedia.org" + link.get("href")
                    linked_page = requests.get(linked_url)
                    linked_soup = BeautifulSoup(linked_page.text, "html.parser")
                    # Find the country information in the linked page
                    country = linked_soup.find("span", {"class": "country-name"})
                    if country:
                        return country.get_text().strip()
            return country
    return "Unknown"

def extract_job(summary):
    """Categorize the person based on job-related keywords with enhanced handling to differentiate between 'Politician' and 'Head of State'."""
    text = summary.lower()

    # Define categories and their associated keywords
    categories = {
        "Scientist": ["scientist", "physicist", "chemist", "biologist", "researcher", "hypothesis", "doctor"],
        "Author": ["author", "writer", "novelist", "playwright", "poet", "bard"],
        "Artist": ["artist", "singer", "musician", "actor", "painter", "director", "dancer", "actress"],
        "Business Leader": ["businessman", "entrepreneur", "executive", "founder", "ceo", "industrialist"],
        "Athlete": ["athlete", "sportsperson", "footballer", "basketball player", "runner", "swimmer", "tennis player", "baseball player", "volleyball player", "track and field athlete", "hockey player"],
        "Religious": ["priest", "pope", "rabbi", "imam", "bible", "reverend", "minister"]
    }

    # Keywords for 'Politician' and 'Head of State'
    political_keywords = {
        "Politician": ["politician", "diplomat", "senator", "governor", "mayor", "congressman", " mp ", "councillor", "secretary", "treasur", "democrat", "republic"],
        "Head of State": ["president", "prime minister", "chancellor", "king", "queen", "emperor", "sultan", "shah", "monarch", "leader"]
    }

    # Function to calculate keyword frequency
    def calculate_keyword_frequency(keywords):
        return sum(text.count(keyword) for keyword in keywords)

    # Calculate scores for non-political categories
    category_scores = {category: calculate_keyword_frequency(keywords) for category, keywords in categories.items()}

    # Determine the primary category from non-political ones
    primary_category = max(category_scores, key=category_scores.get, default=None) if category_scores else None
    max_non_political_score = category_scores.get(primary_category, 0)

    # Calculate scores for political categories
    political_scores = {category: calculate_keyword_frequency(keywords) for category, keywords in political_keywords.items()}
    best_political_category = max(political_scores, key=political_scores.get, default=None) if political_scores else None

    print(political_scores)
    print(category_scores)
    print(max_non_political_score)
    print(political_scores.get("Politician",0))

    # Determine if candidate should be politician at all
    if political_scores.get("Politician",0) > max_non_political_score:
        
        # Decide on the best political category if it is significant
        if best_political_category and political_scores[best_political_category] > max_non_political_score:
            primary_category = best_political_category
  
    return primary_category if primary_category and (category_scores.get(primary_category, 0) + political_scores.get(primary_category, 0)) > 0 else "Unknown"


def main():
    # Load your dataset
    file_path = 'Trivia Draft - Wikipedia_Full_20240414.tsv'  # Change this to the path of your actual file
    df = pd.read_csv(file_path, sep='\t')
    #df = df.head(5)
    
    # print("Step 0: Running Tests")
    # df['Candidate'].apply(test_wikipedia_page_existence)
    
    print("Step 1: Retrieve Wikipedia Context")
    df['HTML Content'] = df['Candidate'].apply(get_wikipedia_html)
    print("Step 2: Parse Key Fields")
    df['Summary'] = df['HTML Content'].apply(extract_summary)  # Extract summary for categorization
    df['Birth Year'] = df['HTML Content'].apply(extract_birth_year)
    #df['Country of Origin'] = df['HTML Content'].apply(extract_country_of_origin)
    df['Job'] = df['Summary'].apply(extract_job)
    
    # Save the updated DataFrame
    df.drop(columns=['HTML Content'], inplace=True)
    df.drop(columns=['Summary'], inplace=True)
    
    print("Step 3: Save New File")
    #print(df)
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
