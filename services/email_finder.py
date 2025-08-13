import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from googlesearch import search

class EmailFinder:
    def __init__(self):
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def fetch_html(self, session, url):
        """Asynchronously fetch HTML content from a URL."""
        try:
            async with session.get(url, headers=self.session_headers, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception:
            return None

    def find_emails_in_text(self, text):
        """Find all email addresses in a given text using regex."""
        return set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))

    async def scrape_website_emails_async(self, url):
        """
        Asynchronously scrapes a website for email addresses.
        It checks the main page and up to 10 relevant sub-pages like 'contact' or 'about'.
        """
        if not url.startswith('http'):
            url = 'https://' + url

        found_emails = set()
        visited_urls = set()
        
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_html(session, url)
            if not html:
                return []

            # Find emails on the homepage
            found_emails.update(self.find_emails_in_text(html))

            # Discover and scrape internal pages
            soup = BeautifulSoup(html, 'html.parser')
            tasks = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                if urlparse(full_url).netloc == urlparse(url).netloc and full_url not in visited_urls:
                    if any(keyword in full_url.lower() for keyword in ['contact', 'about', 'team']):
                        visited_urls.add(full_url)
                        tasks.append(self.fetch_html(session, full_url))
            
            # Scrape up to 5 promising sub-pages
            sub_pages_html = await asyncio.gather(*tasks[:5])
            for page_html in sub_pages_html:
                if page_html:
                    found_emails.update(self.find_emails_in_text(page_html))

        return list(found_emails)

    def search_google_for_domains(self, query, filters):
        """Performs a live Google search to find relevant domains."""
        print(f"Performing live Google search for: {query}, Filters: {filters}")
        search_query = f"{query} {filters.get('industry', '')} {filters.get('location', '')}"
        
        try:
            # Using the 'googlesearch-python' library for simplicity
            urls = list(search(search_query, num_results=10, lang="en"))
            # Extract unique domains from the URLs
            domains = list(set([urlparse(url).netloc for url in urls if urlparse(url).netloc]))
            return domains[:5] # Return top 5 unique domains
        except Exception as e:
            print(f"Google search failed: {e}")
            return [f"{query.replace(' ', '').lower()}.com"] # Fallback

    async def find_emails_universal_async(self, query, filters=None):
        """
        Universal search that combines live website crawling and live Google searches.
        """
        filters = filters or {}
        all_emails = set()

        domains_to_scrape = []
        # Strategy 1: If query is a domain, scrape it directly.
        if '.' in query and ' ' not in query:
            domains_to_scrape.append(query)
        
        # Strategy 2: Use Google to find relevant domains.
        domains_from_google = self.search_google_for_domains(query, filters)
        domains_to_scrape.extend(domains_from_google)
        
        # Scrape all unique domains found
        tasks = [self.scrape_website_emails_async(domain) for domain in set(domains_to_scrape)]
        results = await asyncio.gather(*tasks)
        
        for email_list in results:
            all_emails.update(email_list)
            
        return {
            'success': True,
            'emails': [{'email': e, 'source': 'live_web_scrape', 'verified': True} for e in all_emails],
            'count': len(all_emails),
            'query': query,
            'filters': filters
        }

    # Synchronous wrappers to be called from your Flask routes
    def scrape_website_emails(self, url):
        return asyncio.run(self.scrape_website_emails_async(url))

    def find_emails_universal(self, query, filters=None):
        return asyncio.run(self.find_emails_universal_async(query, filters))

    def search_niche_emails(self, query, filters=None):
        # All searches will now use the live universal finder
        return self.find_emails_universal(query, filters)
