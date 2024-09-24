from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import csv
import os

# Initialize the Chrome WebDriver
driver = webdriver.Chrome()

# Path for the CSV file
csv_file_path = r'C:\Users\DEEPAK\Downloads\match data\player_data.csv'

# Create directory if it does not exist
os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

# Set to keep track of processed countries
processed_countries = set()

def get_player_info(player, label):
    try:
        # Find all divs with the specified class
        info_divs = player.find_elements(By.CSS_SELECTOR, 'div.ds-flex.ds-items-center.ds-space-x-1, div.ds-flex.ds-items-start.ds-space-x-1')
        for div in info_divs:
            # Check if the div contains the label
            if label in div.text:
                # Return the text of the second span (which contains the value)
                return div.find_elements(By.CSS_SELECTOR, 'span')[1].text.strip()
        return "Not Available"
    except Exception:
        return "Not Available"

# Retry Logic Function for Player Scraping
def scrape_players(url, country_name, retries=3):
    for attempt in range(retries):
        try:
            print(f"Going into URL: {url}")
            driver.get(url)
            wait = WebDriverWait(driver, 10)

            # Find all player elements on the page
            players = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.ds-relative.ds-flex.ds-flex-row.ds-space-x-4.ds-p-3')))
            
            if not players:
                print(f"No players found for {country_name}.")
                return False

            # Open CSV file for writing player data
            with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if file.tell() == 0:
                    writer.writerow(['Country', 'Name', 'Role', 'Age', 'Batting Type', 'Bowling Type', 'Image URL'])

                for player in players:
                    try:
                        # Extract player details
                        name = player.find_element(By.CSS_SELECTOR, 'span.ds-text-compact-s.ds-font-bold').text
                        role = player.find_element(By.CSS_SELECTOR, 'p.ds-text-tight-s').text
                        
                        # Use the new function to get age, batting and bowling types
                        age = get_player_info(player, 'Age:')
                        batting_type = get_player_info(player, 'Batting:')
                        bowling_type = get_player_info(player, 'Bowling:')
                        
                        image_url = player.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')

                        # Write player data to CSV
                        writer.writerow([country_name, name, role, age, batting_type, bowling_type, image_url])

                    except Exception as e:
                        print(f"Error processing player: {e}")

            print(f"Successfully scraped data for {country_name}")
            return True  # Indicate successful scraping

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)  # Wait before retrying
            else:
                print(f"Max retries reached for {country_name}, moving to next country.")
                return False  # Indicate failed scraping

# Main Scraper Function for Country Links
def scrape_country_data(base_url):
    while True:
        driver.get(base_url)
        wait = WebDriverWait(driver, 10)

        # Find all country elements on the page
        countries = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.ds-flex.ds-flex-row.ds-space-x-2.ds-items-center')))

        if not countries:
            print("No more countries found. Exiting.")
            break

        found_new_country = False
        for country in countries:
            try:
                country_name = country.find_element(By.TAG_NAME, 'img').get_attribute('alt')
                
                if country_name in processed_countries:
                    continue  # Skip already processed countries
                
                found_new_country = True
                squad_link = country.find_element(By.TAG_NAME, 'a').get_attribute('href')
                squad_link_full = f"https://www.espncricinfo.com{squad_link}" if squad_link.startswith("/") else squad_link

                print(f"Processing new country: {country_name}, Squad Link: {squad_link_full}")
                
                success = scrape_players(squad_link_full, country_name)
                
                if success:
                    processed_countries.add(country_name)
                    print(f"Added {country_name} to processed countries. Total processed: {len(processed_countries)}")
                
                time.sleep(2)  # Wait between countries
                break  # Process one new country per iteration

            except Exception as e:
                print(f"Error scraping country data: {e}")
                continue

        if not found_new_country:
            print("No new countries found. Exiting.")
            break

        time.sleep(5)  # Wait before checking for more countries

# Start scraping from the base URL
base_url = "https://www.espncricinfo.com/series/icc-men-s-t20-world-cup-2024-1411166/squads"

try:
    scrape_country_data(base_url)
finally:
    driver.quit()