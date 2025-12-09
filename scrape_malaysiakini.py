import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time

# Define the keywords to search for
keywords = [
    # Mental health related
    'mental health', 'mental', 'mentally', 'behavioural', 'emotional',
    'psychiatry', 'psychiatric', 'psychiatrist', 'psychology', 'psychological',
    'psychologist', 'counselling', 'counseling', 'counsellor', 'counselor',
    'therapy', 'therapist', 'therapeutic', 'psychotherapy', 'psychotherapeutic',
    'psychotherapists', 'depression', 'depressed', 'suicide', 'suicidal',
    'anxiety', 'anxious', 'stress', 'stressed', 'trauma', 'traumatised',
    'traumatized', 'self-harm', 'stigma', 'resilience', 'discriminate',
    'discrimination', 'discriminated',
    # LGBT+ related
    'lgbt', 'lgbtq', 'lgbtqia', 'lgbtq+', 'lgbtqia+', 'lesbian', 'gay',
    'homosexual', 'homosexuality', 'bisexual', 'bisexuality', 'transgender',
    'transwoman', 'transwomen', 'transman', 'transmen', 'trans', 'transsexual',
    'transvestite', 'non-binary', 'nonbinary', 'queer', 'intersex', 'sogie',
    'sogiesc', 'sex', 'sexual', 'sexuality', 'gender', 'masculine',
    'masculinity', 'feminine', 'femininity'
]

def scrape_malaysiakini(keywords, max_pages=5):
    """
    Scrape Malaysiakini for articles containing specified keywords
    """
    base_url = "https://www.malaysiakini.com"
    results = []
    
    print(f"Starting scrape of Malaysiakini...")
    print(f"Searching for {len(keywords)} keywords")
    print("-" * 60)
    
    # Try to get recent articles from the main page and sections
    sections = ['news', 'columns', 'letters']
    
    for section in sections:
        print(f"\nSearching in section: {section}")
        try:
            url = f"{base_url}/{section}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links (this may need adjustment based on actual site structure)
            articles = soup.find_all('a', href=True)
            
            article_count = 0
            for article in articles:
                link = article.get('href')
                if not link or not link.startswith('/news/'):
                    continue
                
                full_link = base_url + link if link.startswith('/') else link
                title = article.get_text(strip=True)
                
                if not title or len(title) < 10:
                    continue
                
                # Check if any keyword is in the title (case-insensitive)
                title_lower = title.lower()
                matching_keywords = [kw for kw in keywords if kw.lower() in title_lower]
                
                if matching_keywords:
                    article_count += 1
                    result = {
                        'title': title,
                        'url': full_link,
                        'section': section,
                        'matching_keywords': ', '.join(matching_keywords),
                        'date_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    results.append(result)
                    print(f"  ✓ Found: {title[:60]}...")
                
                # Be respectful with requests
                time.sleep(0.5)
            
            print(f"  Found {article_count} matching articles in {section}")
            
        except Exception as e:
            print(f"  Error scraping {section}: {e}")
        
        # Be respectful between sections
        time.sleep(1)
    
    return results

def search_malaysiakini_api(keywords, max_results=50):
    """
    Alternative approach: Use site's search functionality if available
    """
    base_url = "https://www.malaysiakini.com"
    results = []
    
    print("\nTrying search-based approach...")
    
    # Search for each major keyword category
    search_terms = ['mental health', 'lgbt', 'transgender', 'depression', 'anxiety']
    
    for term in search_terms:
        try:
            # This is a generic approach - actual search URL may differ
            search_url = f"{base_url}/search?query={term.replace(' ', '+')}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"  Searching for: {term}")
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Extract search results (structure depends on site)
                # This would need to be customized based on actual HTML structure
                print(f"  Got response for {term}")
            
            time.sleep(2)  # Be respectful
            
        except Exception as e:
            print(f"  Error searching for {term}: {e}")
    
    return results

def save_to_csv(results, filename='malaysiakini_articles.csv'):
    """
    Save results to CSV file
    """
    if not results:
        print("\nNo results to save.")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['title', 'url', 'section', 'matching_keywords', 'date_scraped']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✓ Results saved to {filename}")

def main():
    print("=" * 60)
    print("Malaysiakini News Scraper")
    print("Keywords: Mental Health & LGBT+ related terms")
    print("=" * 60)
    
    # Method 1: Scrape main sections
    results = scrape_malaysiakini(keywords, max_pages=5)
    
    # Display summary
    print("\n" + "=" * 60)
    print(f"SUMMARY")
    print("=" * 60)
    print(f"Total articles found: {len(results)}")
    
    if results:
        print("\nSample results:")
        for i, result in enumerate(results[:5], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Keywords: {result['matching_keywords']}")
        
        # Save to CSV
        save_to_csv(results)
        
        print(f"\n✓ All {len(results)} results saved to CSV")
    else:
        print("\nNo matching articles found.")
        print("\nNote: This script may need customization based on:")
        print("1. Malaysiakini's actual HTML structure")
        print("2. Whether they have anti-scraping measures")
        print("3. Whether you need to handle pagination differently")
    
    print("\n" + "=" * 60)
    print("IMPORTANT NOTES:")
    print("=" * 60)
    print("1. Always check the website's robots.txt and terms of service")
    print("2. Be respectful with request rates (delays are included)")
    print("3. You may need Malaysiakini subscription for full access")
    print("4. Consider using their API if available")
    print("5. This script may need HTML structure updates over time")

if __name__ == "__main__":
    main()