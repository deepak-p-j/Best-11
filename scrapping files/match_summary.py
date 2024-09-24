from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import csv
import re

# Initialize ChromeDriver using the Service class
service = Service(ChromeDriverManager().install())
options = Options()
options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(service=service, options=options)

url = 'https://m.cricbuzz.com/cricket-series/7476/icc-mens-t20-world-cup-2024/matches'
driver.get(url)

# Wait for the page to load
time.sleep(5)

# Locate the match divs using CSS selector
try:
    match_divs = driver.find_elements(By.CSS_SELECTOR, 'a.w-full.bg-cbWhite.flex.flex-col.p-3.gap-1')
except Exception as e:
    print(f"Error finding match divs: {e}")
    driver.quit()
    exit()

# Create a list to store all the matches
matches = []

# Initialize match number
match_no = 1

# Helper function to extract runs, wickets, and overs
def extract_score(score_str):
    default_wickets = '10'
    runs = ''
    wickets = default_wickets
    overs = '0.0'
    
    if '-' in score_str:
        runs_wickets = score_str.split('-')
        runs = runs_wickets[0].strip() if len(runs_wickets) > 0 else ''
        if len(runs_wickets) > 1:
            wickets = runs_wickets[1].split(' ')[0].strip()
    else:
        runs = re.split(r'\s*\(', score_str)[0].strip()
    
    overs_match = re.search(r'\((\d+(\.\d+)?)\)', score_str)
    if overs_match:
        overs = overs_match.group(1)
    
    runs = re.sub(r'\D', '', runs)
    wickets = re.sub(r'\D', '', wickets) if wickets else default_wickets
    
    try:
        overs = float(overs.replace(',', '.'))
    except ValueError:
        overs = 0.0
    
    return runs, wickets, overs

def scrape_matches(url):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    
    # Find all match elements
    match_divs = driver.find_elements(By.CSS_SELECTOR, 'a.w-full.bg-cbWhite.flex.flex-col.p-3.gap-1')
    
    matches = []

    for match_div in match_divs:
        try:
            # Extract match title
            title = match_div.get_attribute('title')
            title_parts = title.split(', ')
            if len(title_parts) >= 3:
                team1, team2 = title_parts[0].split(' vs ')
                match_no = title_parts[1].replace('Match ', '')
                group = title_parts[2].replace('Group ', '')
            else:
                team1, team2 = 'NA', 'NA'
                match_no, group = 'NA', 'NA'
            
            # Extract venue
            venue_div = match_div.find_element(By.CSS_SELECTOR, 'div.text-xs.text-cbTxtSec.dark:text-cbTxtSec')
            venue = venue_div.text.split('•')[-1].strip() if '•' in venue_div.text else 'NA'
            
            # Extract scores
            score_divs = match_div.find_elements(By.CSS_SELECTOR, 'div.flex.flex-col.gap-3.my-2 > div')
            if len(score_divs) == 2:
                team1_score = score_divs[0].text
                team2_score = score_divs[1].text
                team1_runs, team1_wickets, team1_overs = extract_score(team1_score)
                team2_runs, team2_wickets, team2_overs = extract_score(team2_score)
            else:
                team1_runs, team1_wickets, team1_overs = 'NA', 'NA', 'NA'
                team2_runs, team2_wickets, team2_overs = 'NA', 'NA', 'NA'
            
            # Extract match result
            result_text = match_div.find_element(By.CSS_SELECTOR, 'span.text-cbComplete').text
            if 'won' in result_text:
                margin = re.search(r'by (.+)', result_text)
                winner = result_text
                margin = margin.group(1) if margin else 'NA'
            else:
                winner = result_text
                margin = 'NA'
                # Set scores and overs to 'NA' if the match result doesn't contain 'won'
                team1_runs, team1_wickets, team1_overs = 'NA', 'NA', 'NA'
                team2_runs, team2_wickets, team2_overs = 'NA', 'NA', 'NA'
            
            # Append to matches list
            matches.append([team1, team2, match_no, group, venue, team1_runs, team1_wickets, team1_overs, team2_runs, team2_wickets, team2_overs, margin, winner])
        
        except Exception as e:
            print(f"Error parsing match: {e}")
            matches.append(['NA'] * 13)  # Fill with 'NA' in case of an error

    driver.quit()
    
    return matches


def save_to_csv(matches, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        header = ['Team 1', 'Team 2', 'Match No', 'Group', 'Venue', 'Team 1 Runs', 'Team 1 Wickets', 'Team 1 Overs', 'Team 2 Runs', 'Team 2 Wickets', 'Team 2 Overs', 'Margin', 'Winner']
        writer.writerow(header)
        writer.writerows(matches)

if __name__ == "__main__":
    url = 'https://m.cricbuzz.com/cricket-series/7476/icc-mens-t20-world-cup-2024/matches'
    matches = scrape_matches(url)
    save_to_csv(matches, 'C:\\Users\\DEEPAK\\Downloads\\match data\\match_summary.csv')

print("Data saved to 'C:\\Users\\DEEPAK\\Downloads\\match data\\match_summary.csv' successfully!")

# Close the driver
driver.quit()
