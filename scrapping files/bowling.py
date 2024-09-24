import time
import os
import csv
import traceback
import re
import unicodedata
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Set up Chrome options
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment for headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Base URL
base_url = 'https://www.espncricinfo.com/series/icc-men-s-t20-world-cup-2024-1411166/match-schedule-fixtures-and-results'

# Folder path for saving CSV
folder_path = r'C:\Users\DEEPAK\Downloads\match data'
bowling_csv_file = os.path.join(folder_path, 'bowling_stats.csv')

# CSV header
bowling_csv_header = ['match_id', 'match', 'team', 'name', 'overs', 'maidens', 'runs', 'wickets', 'economy', 'dots', 'fours', 'sixes', 'wides', 'no_balls']

# Initialize bowling_stats dictionary
bowling_stats = {}

def wait_for_element(driver, selector, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )

def clean_text(text):
    # Remove content within parentheses
    text = re.sub(r'\s*\([^)]*\)', '', text)
    
    # Remove plus symbol from the beginning of the text
    text = re.sub(r'^\+\s*', '', text)
    
    # Remove or replace non-ASCII characters
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove any remaining non-alphanumeric characters (except spaces)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def save_to_csv(data):
    try:
        # Check if the folder exists, if not create it
        os.makedirs(os.path.dirname(bowling_csv_file), exist_ok=True)
        
        file_exists = os.path.isfile(bowling_csv_file)
        
        print(f"Attempting to save data for {data['name']} to {bowling_csv_file}")
        
        mode = 'a' if file_exists else 'w'
        with open(bowling_csv_file, mode=mode, newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=bowling_csv_header)
            if not file_exists:
                writer.writeheader()
                print("Writing CSV header")
            writer.writerow(data)
        print(f"Successfully saved data for {data['name']} to CSV")
    except Exception as e:
        print(f"Error saving to CSV: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Attempting to save to: {bowling_csv_file}")
        print(f"Data being saved: {data}")
        print(traceback.format_exc())

def extract_bowling_stats(team_name, innings):
    global bowling_stats
    try:
        # Find all tables in the innings
        tables = innings.find_elements(By.CSS_SELECTOR, 'table.ds-w-full.ds-table.ds-table-md.ds-table-auto')
        
        bowling_table = None
        for table in tables:
            # Check if the first column header is "Bowling"
            try:
                first_header = table.find_element(By.CSS_SELECTOR, 'thead th:first-child').text.strip()
                if first_header == "Bowling":
                    bowling_table = table
                    break
            except NoSuchElementException:
                continue
        
        if not bowling_table:
            print(f"No bowling table found for {team_name}")
            return

        rows = bowling_table.find_elements(By.CSS_SELECTOR, 'tbody tr')
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, 'td')
            if len(columns) >= 11:  # Ensure we have enough columns
                bowler_name = clean_text(columns[0].text)
                overs = columns[1].text
                maidens = columns[2].text
                runs = columns[3].text
                wickets = columns[4].text
                economy = columns[5].text
                dots = columns[6].text
                fours = columns[7].text
                sixes = columns[8].text
                wides = columns[9].text
                no_balls = columns[10].text

                # Create a unique identifier for each bowler
                bowler_id = f"{match_id}_{team_name}_{bowler_name}"

                # Store the data in the bowling_stats dictionary
                bowling_stats[bowler_id] = {
                    'match_id': match_id,
                    'match': match_name,
                    'team': team_name,
                    'name': bowler_name,
                    'overs': overs,
                    'maidens': maidens,
                    'runs': runs,
                    'wickets': wickets,
                    'economy': economy,
                    'dots': dots,
                    'fours': fours,
                    'sixes': sixes,
                    'wides': wides,
                    'no_balls': no_balls
                }
                print(f"Extracted bowling stats for {bowler_name}")
                
                # Save the data to CSV
                save_to_csv(bowling_stats[bowler_id])
    except Exception as e:
        print(f"Error extracting bowling stats for {team_name}: {str(e)}")
        print(f"Innings HTML: {innings.get_attribute('outerHTML')}")
        traceback.print_exc()

def scrape_matches():
    global match_name, match_id
    driver.get(base_url)
    time.sleep(5)  # Initial wait for page load

    match_links_scraped = set()
    match_counter = 1

    while True:
        # Get current match divs on the page
        match_divs = driver.find_elements(By.CSS_SELECTOR, 'div.ds-p-4.hover\\:ds-bg-ui-fill-translucent')
        
        if not match_divs:
            print("No more matches found. Exiting.")
            break

        for match_div in match_divs:
            try:
                match_url_element = match_div.find_element(By.CSS_SELECTOR, 'a')
                match_url = match_url_element.get_attribute('href')
                
                if match_url in match_links_scraped:
                    continue
                
                match_links_scraped.add(match_url)
                print(f"Navigating to match URL: {match_url}")
                
                # Open match URL in a new tab
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(match_url)
                
                # Wait for the title element to be present
                title_element = wait_for_element(driver, 'h1.ds-text-title-xs.ds-font-bold')
                match_title = title_element.text
                print(f"Match Title: {match_title}")
                
                match_name = clean_text(match_title.split(',')[0])
                match_id = str(match_counter)
                match_counter += 1
                
                # Extract team names and bowling statistics
                innings_elements = driver.find_elements(By.CSS_SELECTOR, 'div.ds-rounded-lg.ds-mt-2')
                print(f"Found {len(innings_elements)} innings elements")
                for innings in innings_elements:
                    try:
                        team_name_element = innings.find_element(By.CSS_SELECTOR, 'span.ds-text-title-xs.ds-font-bold.ds-capitalize')
                        team_name = clean_text(team_name_element.text)
                        print(f"Processing team: {team_name}")
                        
                        # Extract bowling stats
                        extract_bowling_stats(team_name, innings)
                    except Exception as e:
                        print(f"Error processing innings: {str(e)}")
                        print(f"Innings HTML: {innings.get_attribute('outerHTML')}")
                        traceback.print_exc()
                
                # Close the tab and switch back to the main window
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
            except Exception as e:
                print(f"Error scraping match: {str(e)}")
                traceback.print_exc()
                continue
        
        # Check if there's a "Show More" button and click it
        try:
            show_more_button = wait_for_element(driver, 'button.ds-button.ds-text-center.ds-uppercase.ds-font-bold.ds-border-none.ds-bg-fill-primary', timeout=5)
            driver.execute_script("arguments[0].click();", show_more_button)
            time.sleep(3)  # Wait for new content to load
        except TimeoutException:
            print("No more 'Show More' button found. Exiting.")
            break
        except Exception as e:
            print(f"Error clicking 'Show More' button: {str(e)}")
            traceback.print_exc()
            break

try:
    scrape_matches()
finally:
    driver.quit()