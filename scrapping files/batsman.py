import time
import os
import csv
import traceback
import re
import unicodedata
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
csv_file = os.path.join(folder_path, 'batting_stats.csv')

# CSV header
csv_header = ['match_id', 'match', 'team', 'bat_pos', 'name', 'not_out', 'runs', 'balls', 'minutes', 'fours', 'sixes', 'strike_rate']

def wait_for_element(driver, selector, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )

def save_to_csv(data):
    try:
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=csv_header)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
        print(f"Successfully saved data for {data['name']} to CSV")
    except Exception as e:
        print(f"Error saving to CSV: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Attempting to save to: {csv_file}")
        print(f"Data being saved: {data}")
        traceback.print_exc()

def clean_text(text):
    # Remove content within parentheses
    text = re.sub(r'\s*\([^)]*\)', '', text)
    
    # Remove plus symbol from the beginning of the text
    text = re.sub(r'^\†\s*', '', text)
    
    # Remove or replace non-ASCII characters
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove any remaining non-alphanumeric characters (except spaces)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def extract_batting_stats(team_name, table):
    rows = table.find_elements(By.TAG_NAME, 'tr')
    print(f"Found {len(rows)} rows for team {team_name}")
    
    if len(rows) == 0:
        print(f"No rows found. Table HTML: {table.get_attribute('outerHTML')}")
        return

    bat_pos = 1  # Initialize batting position counter

    for row in rows:
        try:
            # Check if this is a valid batsman row
            columns = row.find_elements(By.TAG_NAME, 'td')
            if len(columns) < 8:
                continue  # Skip rows that don't have enough columns

            # Extract batsman name
            name_element = columns[0]
            name = clean_text(name_element.text)

            # Determine if batsman is not out
            dismissal_element = columns[1]
            not_out = 'not out' in dismissal_element.text.lower()
            
            # Extract other stats
            runs = columns[2].text.strip()
            balls = columns[3].text.strip()
            
            # Minutes might be hidden, so we need to handle potential exceptions
            try:
                minutes = columns[4].text.strip()
            except IndexError:
                minutes = 'N/A'
            
            fours = columns[5].text.strip()
            sixes = columns[6].text.strip()
            strike_rate = columns[7].text.strip()

            print(f"Extracted data for batsman: {name} (Position: {bat_pos})")
            
            batting_data = {
                'match_id': match_id,
                'match': match_name,
                'team': team_name,
                'bat_pos': bat_pos,
                'name': name,
                'not_out': 'Not Out' if not_out else 'Out',
                'runs': runs,
                'balls': balls,
                'minutes': minutes,
                'fours': fours,
                'sixes': sixes,
                'strike_rate': strike_rate
            }
            
            save_to_csv(batting_data)
            
            bat_pos += 1  # Increment batting position for the next valid row
            
        except Exception as e:
            print(f"Error extracting batting stats: {str(e)}")
            print(f"Row HTML: {row.get_attribute('outerHTML')}")
            traceback.print_exc()

def scrape_matches():
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
                
                global match_name, match_id
                match_name = clean_text(match_title.split(',')[0])
                match_id = str(match_counter)
                match_counter += 1
                
                # Extract team names and batting statistics
                innings_elements = driver.find_elements(By.CSS_SELECTOR, 'div.ds-rounded-lg.ds-mt-2')
                print(f"Found {len(innings_elements)} innings elements")
                for innings in innings_elements:
                    try:
                        team_name_element = innings.find_element(By.CSS_SELECTOR, 'span.ds-text-title-xs.ds-font-bold.ds-capitalize')
                        team_name = clean_text(team_name_element.text)
                        print(f"Processing team: {team_name}")
                        batting_table = innings.find_element(By.CSS_SELECTOR, 'table.ci-scorecard-table')
                        extract_batting_stats(team_name, batting_table)
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

    print(f"Scraping completed. Data should be saved to {csv_file}")

# Run the scraping function
scrape_matches()

# Close the driver after scraping is done
driver.quit()