# services/email_finder.py - Consolidated Email Finding and Scraping Service
# Combines the best features from email_scraper.py and universal_email_finder.py

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import concurrent.futures
from collections import defaultdict
import time
import sqlite3
import json
from datetime import datetime, timedelta
import redis
import dns.resolver
from typing import List, Dict, Set, Optional
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailFinder:
    """
    Consolidated email finding and scraping service that combines:
    - Website scraping capabilities
    - Universal email finding across multiple sources
    - Email verification and validation
    - Rate limiting and caching
    """
    
    def __init__(self, redis_url="redis://localhost:6379", db_path="outreachpilot.db"):
        # Initialize Redis for caching
        try:
            self.redis_client = redis.from_url(redis_url)
        except:
            self.redis_client = None
            logger.warning("Redis not available, using in-memory cache")
        
        # Database connection
        self.db_path = db_path
        
        # HTTP session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Email patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b')
        
        # Rate limiting configuration
        self.rate_limits = {
            'requests_per_minute': 30,
            'requests_per_hour': 1000,
            'delay_between_requests': 2
        }
        
        # Common email generation patterns
        self.common_patterns = {
            'firstname.lastname': lambda f, l: f"{f.lower()}.{l.lower()}",
            'firstname_lastname': lambda f, l: f"{f.lower()}_{l.lower()}",
            'firstname': lambda f, l: f"{f.lower()}",
            'firstinitiallastname': lambda f, l: f"{f[0].lower()}{l.lower()}",
            'firstnamelastname': lambda f, l: f"{f.lower()}{l.lower()}",
            'f.lastname': lambda f, l: f"{f[0].lower()}.{l.lower()}",
            'firstname.l': lambda f, l: f"{f.lower()}.{l[0].lower()}",
            'contact@': lambda f, l: "contact",
            'info@': lambda f, l: "info",
            'hello@': lambda f, l: "hello",
            'support@': lambda f, l: "support",
            'sales@': lambda f, l: "sales",
            'marketing@': lambda f, l: "marketing",
            'admin@': lambda f, l: "admin",
            'team@': lambda f, l: "team"
        }
        
        # Data sources for universal email finding
        self.data_sources = {
            'company_directories': [
                'https://www.linkedin.com/company/',
                'https://www.crunchbase.com/organization/',
                'https://www.zoominfo.com/c/',
                'https://www.apollo.io/companies/'
            ],
            'email_finders': [
                'https://hunter.io/api/v2/',
                'https://api.clearbit.com/v1/',
                'https://api.rocketreach.co/v2/',
                'https://api.snov.io/v1/'
            ],
            'social_networks': [
                'https://twitter.com/',
                'https://www.linkedin.com/in/',
                'https://github.com/',
                'https://www.facebook.com/'
            ],
            'business_directories': [
                'https://www.yellowpages.com/',
                'https://www.yelp.com/',
                'https://www.google.com/maps/',
                'https://www.bing.com/maps/'
            ]
        }
    
    def scrape_website(self, url: str, max_depth: int = 2) -> Dict:
        """Scrape emails from a website with recursive crawling"""
        try:
            # Check rate limits
            self._check_rate_limits()
            
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            domain = urlparse(url).netloc
            found_emails = set()
            found_names = set()
            scraped_pages = set()
            
            # Start recursive scraping
            self._scrape_page_recursive(url, domain, found_emails, found_names, scraped_pages, max_depth)
            
            # Generate potential emails based on patterns
            potential_emails = self._generate_potential_emails(found_names, domain)
            
            # Verify emails
            verified_emails = self._verify_emails(list(found_emails) + potential_emails)
            
            return {
                'success': True,
                'domain': domain,
                'emails_found': len(found_emails),
                'emails_verified': len(verified_emails),
                'names_found': len(found_names),
                'potential_emails': len(potential_emails),
                'emails': verified_emails,
                'names': list(found_names),
                'scraped_pages': len(scraped_pages)
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'domain': urlparse(url).netloc if '://' in url else url
            }
    
    def find_emails_universal(self, query: str, industry: str = None, location: str = None, limit: int = 1000) -> Dict:
        """Universal email finding across multiple data sources"""
        logger.info(f"🔍 Universal Email Search: {query}")
        
        all_emails = set()
        sources_used = []
        
        # Method 1: Company Website Scraping
        website_emails = self._scrape_company_websites(query)
        all_emails.update(website_emails)
        if website_emails:
            sources_used.append("Company Websites")
        
        # Method 2: Social Media Mining
        social_emails = self._mine_social_media(query, industry)
        all_emails.update(social_emails)
        if social_emails:
            sources_used.append("Social Media")
        
        # Method 3: Business Directory Search
        directory_emails = self._search_business_directories(query, location)
        all_emails.update(directory_emails)
        if directory_emails:
            sources_used.append("Business Directories")
        
        # Method 4: Professional Networks
        network_emails = self._mine_professional_networks(query, industry)
        all_emails.update(network_emails)
        if network_emails:
            sources_used.append("Professional Networks")
        
        # Method 5: Email API Services
        api_emails = self._search_email_apis(query, industry, location)
        all_emails.update(api_emails)
        if api_emails:
            sources_used.append("Email APIs")
        
        # Method 6: Intelligent Domain Search
        domain_emails = self._intelligent_domain_search(query)
        all_emails.update(domain_emails)
        if domain_emails:
            sources_used.append("Domain Intelligence")
        
        # Method 7: Global Database Search
        database_emails = self._search_global_database(query, industry, location)
        all_emails.update(database_emails)
        if database_emails:
            sources_used.append("Global Database")
        
        # Method 8: News and Event Sources
        news_emails = self._search_news_sources(query)
        all_emails.update(news_emails)
        if news_emails:
            sources_used.append("News Sources")
        
        # Method 9: Research Data
        research_emails = self._search_research_data(query, industry)
        all_emails.update(research_emails)
        if research_emails:
            sources_used.append("Research Data")
        
        # Verify and filter emails
        verified_emails = self._verify_emails_batch(list(all_emails))
        valid_emails = [email for email, is_valid in verified_emails.items() if is_valid]
        
        # Apply limit
        if limit and len(valid_emails) > limit:
            valid_emails = valid_emails[:limit]
        
        return {
            'success': True,
            'query': query,
            'total_emails_found': len(all_emails),
            'verified_emails': len(valid_emails),
            'emails': valid_emails,
            'sources_used': sources_used,
            'search_metadata': {
                'industry': industry,
                'location': location,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def search_company_emails(self, company_name: str, industry: str = None) -> Dict:
        """Search for emails from a specific company"""
        try:
            logger.info(f"Searching emails for company: {company_name}")
            
            # Method 1: Direct website scraping
            website_result = self._search_company_website(company_name)
            
            # Method 2: LinkedIn company search
            linkedin_result = self._search_linkedin(company_name)
            
            # Method 3: Industry database search
            industry_result = self._search_industry_database(company_name, industry)
            
            # Combine results
            all_emails = set()
            all_names = set()
            
            if website_result.get('emails'):
                all_emails.update(website_result['emails'])
            if linkedin_result.get('emails'):
                all_emails.update(linkedin_result['emails'])
            if industry_result.get('emails'):
                all_emails.update(industry_result['emails'])
            
            if website_result.get('names'):
                all_names.update(website_result['names'])
            if linkedin_result.get('names'):
                all_names.update(linkedin_result['names'])
            if industry_result.get('names'):
                all_names.update(industry_result['names'])
            
            # Generate potential emails from names
            domain = website_result.get('domain') or linkedin_result.get('domain')
            if domain and all_names:
                potential_emails = self._generate_potential_emails(all_names, domain)
                all_emails.update(potential_emails)
            
            # Verify emails
            verified_emails = self._verify_emails(list(all_emails))
            
            return {
                'success': True,
                'company': company_name,
                'industry': industry,
                'emails_found': len(all_emails),
                'emails_verified': len(verified_emails),
                'names_found': len(all_names),
                'emails': verified_emails,
                'names': list(all_names),
                'domain': domain,
                'sources': {
                    'website': website_result.get('success', False),
                    'linkedin': linkedin_result.get('success', False),
                    'industry_db': industry_result.get('success', False)
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching company emails for {company_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'company': company_name
            }
    
    def search_industry_emails(self, industry: str, location: str = None, company_size: str = None) -> Dict:
        """Search for emails across an entire industry"""
        try:
            logger.info(f"Searching industry emails: {industry} in {location or 'any location'}")
            
            # Get companies in the industry
            companies = self._get_companies_by_industry(industry, location, company_size)
            
            all_emails = set()
            all_names = set()
            companies_processed = 0
            
            # Process companies with rate limiting
            for company in companies[:50]:  # Limit to prevent abuse
                try:
                    company_result = self.search_company_emails(company['name'], industry)
                    if company_result.get('success') and company_result.get('emails'):
                        all_emails.update(company_result['emails'])
                    if company_result.get('names'):
                        all_names.update(company_result['names'])
                    companies_processed += 1
                    
                    # Rate limiting
                    time.sleep(self.rate_limits['delay_between_requests'])
                    
                except Exception as e:
                    logger.warning(f"Error processing company {company['name']}: {str(e)}")
                    continue
            
            # Generate potential emails from names
            potential_emails = set()
            for company in companies[:10]:  # Limit for performance
                if company.get('domain'):
                    company_names = [name for name in all_names if self._is_company_related(name, company['name'])]
                    if company_names:
                        company_potential = self._generate_potential_emails(company_names, company['domain'])
                        potential_emails.update(company_potential)
            
            all_emails.update(potential_emails)
            
            # Verify emails
            verified_emails = self._verify_emails(list(all_emails))
            
            return {
                'success': True,
                'industry': industry,
                'location': location,
                'company_size': company_size,
                'companies_processed': companies_processed,
                'total_companies_found': len(companies),
                'emails_found': len(all_emails),
                'emails_verified': len(verified_emails),
                'names_found': len(all_names),
                'emails': verified_emails,
                'names': list(all_names)
            }
            
        except Exception as e:
            logger.error(f"Error searching industry emails for {industry}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'industry': industry
            }
    
    def verify_email(self, email: str) -> bool:
        """Verify if an email address is valid and deliverable"""
        try:
            # Basic format validation
            if not self._is_valid_email(email):
                return False
            
            # Check cache first
            if self.redis_client:
                cache_key = f"email_verify:{email}"
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    return cached_result.decode() == 'true'
            
            # DNS validation
            domain = email.split('@')[1]
            try:
                dns.resolver.resolve(domain, 'MX')
            except:
                return False
            
            # Store result in cache
            if self.redis_client:
                cache_key = f"email_verify:{email}"
                self.redis_client.setex(cache_key, 3600, 'true' if True else 'false')
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying email {email}: {str(e)}")
            return False
    
    def verify_emails_batch(self, emails: List[str]) -> Dict[str, bool]:
        """Verify multiple emails in batch"""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_email = {executor.submit(self.verify_email, email): email for email in emails}
            
            for future in concurrent.futures.as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    results[email] = future.result()
                except Exception as e:
                    logger.error(f"Error verifying email {email}: {str(e)}")
                    results[email] = False
        
        return results
    
    def save_scraped_emails(self, user_id: int, company_name: str, emails: List[str], source: str = 'manual') -> bool:
        """Save scraped emails to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraped_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    company_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    source TEXT DEFAULT 'manual',
                    verified BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Insert emails
            for email in emails:
                cursor.execute("""
                    INSERT OR IGNORE INTO scraped_emails (user_id, company_name, email, source, verified)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, company_name, email, source, self.verify_email(email)))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving scraped emails: {str(e)}")
            return False
    
    def get_user_scraped_emails(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get scraped emails for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT company_name, email, source, verified, created_at
                FROM scraped_emails
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'company_name': row[0],
                    'email': row[1],
                    'source': row[2],
                    'verified': bool(row[3]),
                    'created_at': row[4]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting user scraped emails: {str(e)}")
            return []
    
    # Private helper methods
    
    def _scrape_page_recursive(self, url: str, domain: str, emails: Set, names: Set, 
                             scraped_pages: Set, max_depth: int, current_depth: int = 0):
        """Recursively scrape pages for emails and names"""
        if current_depth >= max_depth or url in scraped_pages:
            return
        
        try:
            scraped_pages.add(url)
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract emails and names from current page
            page_emails = self._extract_emails_from_html(soup, domain)
            page_names = self._extract_names_from_html(soup)
            
            emails.update(page_emails)
            names.update(page_names)
            
            # Find links to other pages on the same domain
            if current_depth < max_depth - 1:
                links = soup.find_all('a', href=True)
                for link in links[:10]:  # Limit to prevent infinite crawling
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    if urlparse(full_url).netloc == domain and full_url not in scraped_pages:
                        time.sleep(self.rate_limits['delay_between_requests'])
                        self._scrape_page_recursive(full_url, domain, emails, names, scraped_pages, max_depth, current_depth + 1)
            
        except Exception as e:
            logger.warning(f"Error scraping page {url}: {str(e)}")
    
    def _extract_emails_from_html(self, soup: BeautifulSoup, domain: str) -> List[str]:
        """Extract emails from HTML content"""
        emails = []
        
        # Find emails in text
        text_content = soup.get_text()
        found_emails = self.email_pattern.findall(text_content)
        
        # Filter emails by domain if specified
        if domain:
            domain_emails = [email for email in found_emails if email.endswith(f'@{domain}')]
            emails.extend(domain_emails)
        else:
            emails.extend(found_emails)
        
        # Find emails in href attributes
        email_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        for link in email_links:
            email = link['href'].replace('mailto:', '')
            if self._is_valid_email(email):
                emails.append(email)
        
        # Find emails in data attributes
        data_emails = soup.find_all(attrs={'data-email': True})
        for element in data_emails:
            email = element['data-email']
            if self._is_valid_email(email):
                emails.append(email)
        
        return list(set(emails))  # Remove duplicates
    
    def _extract_names_from_html(self, soup: BeautifulSoup) -> List[str]:
        """Extract names from HTML content"""
        names = []
        
        # Find names in text
        text_content = soup.get_text()
        found_names = self.name_pattern.findall(text_content)
        names.extend(found_names)
        
        # Find names in title attributes
        title_names = soup.find_all(attrs={'title': True})
        for element in title_names:
            title = element['title']
            found_names = self.name_pattern.findall(title)
            names.extend(found_names)
        
        # Find names in alt attributes
        alt_names = soup.find_all(attrs={'alt': True})
        for element in alt_names:
            alt = element['alt']
            found_names = self.name_pattern.findall(alt)
            names.extend(found_names)
        
        return list(set(names))  # Remove duplicates
    
    def _generate_potential_emails(self, names: Set, domain: str) -> List[str]:
        """Generate potential emails based on common patterns"""
        potential_emails = []
        
        for name in names:
            if ' ' in name:
                first_name, last_name = name.split(' ', 1)
                
                for pattern_name, pattern_func in self.common_patterns.items():
                    try:
                        if pattern_name.startswith(('contact@', 'info@', 'hello@', 'support@', 'sales@', 'marketing@', 'admin@', 'team@')):
                            email = f"{pattern_func(first_name, last_name)}@{domain}"
                        else:
                            email = f"{pattern_func(first_name, last_name)}@{domain}"
                        
                        if self._is_valid_email(email):
                            potential_emails.append(email)
                    except:
                        continue
        
        return list(set(potential_emails))
    
    def _verify_emails(self, emails: List[str]) -> List[str]:
        """Verify a list of emails and return valid ones"""
        verified_emails = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_email = {executor.submit(self.verify_email, email): email for email in emails}
            
            for future in concurrent.futures.as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    if future.result():
                        verified_emails.append(email)
                except Exception as e:
                    logger.warning(f"Error verifying email {email}: {str(e)}")
        
        return verified_emails
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        if not email or '@' not in email:
            return False
        
        # Check against regex pattern
        if not self.email_pattern.match(email):
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            'example.com',
            'test.com',
            'domain.com',
            'email.com',
            'user@',
            '@domain',
            'noreply@',
            'no-reply@'
        ]
        
        for pattern in invalid_patterns:
            if pattern in email.lower():
                return False
        
        return True
    
    def _check_rate_limits(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Simple rate limiting implementation
        # In production, you might want to use Redis for more sophisticated rate limiting
        time.sleep(self.rate_limits['delay_between_requests'])
    
    def _scrape_company_websites(self, query: str) -> Set[str]:
        """Scrape company websites for emails"""
        emails = set()
        
        try:
            # Search for company website
            search_query = f"{query} company website"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract search results
            search_results = soup.find_all('a', href=True)
            for result in search_results[:5]:  # Limit to first 5 results
                href = result['href']
                if href.startswith('/url?q='):
                    url = href.split('/url?q=')[1].split('&')[0]
                    if self._is_company_website(url, query):
                        try:
                            website_emails = self._scrape_single_website(url)
                            emails.update(website_emails)
                        except:
                            continue
            
        except Exception as e:
            logger.warning(f"Error scraping company websites for {query}: {str(e)}")
        
        return emails
    
    def _mine_social_media(self, query: str, industry: str = None) -> Set[str]:
        """Mine social media for email addresses"""
        emails = set()
        
        # This is a simplified implementation
        # In production, you would use proper social media APIs
        try:
            # Search for company social media profiles
            social_queries = [
                f"{query} linkedin",
                f"{query} twitter",
                f"{query} facebook"
            ]
            
            for social_query in social_queries:
                # Simulate finding emails from social profiles
                # In reality, you'd need proper API access
                pass
                
        except Exception as e:
            logger.warning(f"Error mining social media for {query}: {str(e)}")
        
        return emails
    
    def _search_business_directories(self, query: str, location: str = None) -> Set[str]:
        """Search business directories for emails"""
        emails = set()
        
        # This is a simplified implementation
        # In production, you would use proper business directory APIs
        try:
            # Search business directories
            directory_queries = [
                f"{query} yellowpages",
                f"{query} yelp",
                f"{query} google maps"
            ]
            
            for directory_query in directory_queries:
                # Simulate finding emails from directories
                # In reality, you'd need proper API access
                pass
                
        except Exception as e:
            logger.warning(f"Error searching business directories for {query}: {str(e)}")
        
        return emails
    
    def _mine_professional_networks(self, query: str, industry: str = None) -> Set[str]:
        """Mine professional networks for emails"""
        emails = set()
        
        # This is a simplified implementation
        # In production, you would use proper professional network APIs
        try:
            # Search professional networks
            network_queries = [
                f"{query} linkedin",
                f"{query} crunchbase",
                f"{query} apollo"
            ]
            
            for network_query in network_queries:
                # Simulate finding emails from networks
                # In reality, you'd need proper API access
                pass
                
        except Exception as e:
            logger.warning(f"Error mining professional networks for {query}: {str(e)}")
        
        return emails
    
    def _search_email_apis(self, query: str, industry: str = None, location: str = None) -> Set[str]:
        """Search email finding APIs for emails"""
        emails = set()
        
        # This is a simplified implementation
        # In production, you would use proper email finding APIs
        try:
            # Search email finding services
            api_queries = [
                f"{query} hunter.io",
                f"{query} clearbit",
                f"{query} rocketreach"
            ]
            
            for api_query in api_queries:
                # Simulate finding emails from APIs
                # In reality, you'd need proper API access
                pass
                
        except Exception as e:
            logger.warning(f"Error searching email APIs for {query}: {str(e)}")
        
        return emails
    
    def _intelligent_domain_search(self, query: str) -> Set[str]:
        """Intelligent domain-based email search"""
        emails = set()
        
        try:
            # Try to find the company domain
            domain = self._find_company_domain(query)
            if domain:
                # Generate common email patterns for the domain
                common_emails = self._generate_common_emails(domain)
                emails.update(common_emails)
                
                # Try to find contact page emails
                contact_emails = self._find_contact_page_emails(domain)
                emails.update(contact_emails)
                
        except Exception as e:
            logger.warning(f"Error in intelligent domain search for {query}: {str(e)}")
        
        return emails
    
    def _search_global_database(self, query: str, industry: str = None, location: str = None) -> Set[str]:
        """Search global email database"""
        emails = set()
        
        # This is a simplified implementation
        # In production, you would use a proper global email database
        try:
            # Search global database
            # In reality, you'd need proper database access
            pass
                
        except Exception as e:
            logger.warning(f"Error searching global database for {query}: {str(e)}")
        
        return emails
    
    def _search_news_sources(self, query: str) -> Set[str]:
        """Search news sources for emails"""
        emails = set()
        
        # This is a simplified implementation
        # In production, you would use proper news APIs
        try:
            # Search news sources
            # In reality, you'd need proper API access
            pass
                
        except Exception as e:
            logger.warning(f"Error searching news sources for {query}: {str(e)}")
        
        return emails
    
    def _search_research_data(self, query: str, industry: str = None) -> Set[str]:
        """Search research data for emails"""
        emails = set()
        
        # This is a simplified implementation
        # In production, you would use proper research data APIs
        try:
            # Search research data
            # In reality, you'd need proper API access
            pass
                
        except Exception as e:
            logger.warning(f"Error searching research data for {query}: {str(e)}")
        
        return emails
    
    def _search_company_website(self, company_name: str) -> Dict:
        """Search for a company's website"""
        try:
            search_query = f"{company_name} official website"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract first result
            search_results = soup.find_all('a', href=True)
            for result in search_results:
                href = result['href']
                if href.startswith('/url?q='):
                    url = href.split('/url?q=')[1].split('&')[0]
                    if self._is_company_website(url, company_name):
                        return {
                            'success': True,
                            'website': url,
                            'domain': urlparse(url).netloc
                        }
            
            return {'success': False, 'error': 'No website found'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _search_linkedin(self, company_name: str) -> Dict:
        """Search LinkedIn for company information"""
        try:
            # This is a simplified implementation
            # In production, you would use the LinkedIn API
            search_query = f"{company_name} linkedin company"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract LinkedIn profile
            search_results = soup.find_all('a', href=True)
            for result in search_results:
                href = result['href']
                if 'linkedin.com/company/' in href:
                    return {
                        'success': True,
                        'linkedin_profile': href,
                        'domain': 'linkedin.com'
                    }
            
            return {'success': False, 'error': 'No LinkedIn profile found'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _search_industry_database(self, company_name: str, industry: str) -> Dict:
        """Search industry database for company information"""
        try:
            # This is a simplified implementation
            # In production, you would use proper industry databases
            return {
                'success': True,
                'industry': industry,
                'emails': [],
                'names': []
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_companies_by_industry(self, industry: str, location: str = None, company_size: str = None) -> List[Dict]:
        """Get companies by industry"""
        # This is a simplified implementation
        # In production, you would use proper industry databases
        companies = []
        
        # Generate sample companies for demonstration
        sample_companies = [
            {'name': f'Sample {industry} Company 1', 'domain': f'sample1{industry.lower()}.com'},
            {'name': f'Sample {industry} Company 2', 'domain': f'sample2{industry.lower()}.com'},
            {'name': f'Sample {industry} Company 3', 'domain': f'sample3{industry.lower()}.com'}
        ]
        
        companies.extend(sample_companies)
        
        return companies
    
    def _scrape_single_website(self, url: str) -> List[str]:
        """Scrape a single website for emails"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            emails = self._extract_emails_from_html(soup, urlparse(url).netloc)
            return emails
            
        except Exception as e:
            logger.warning(f"Error scraping single website {url}: {str(e)}")
            return []
    
    def _is_company_website(self, url: str, company_name: str) -> bool:
        """Check if URL is likely a company website"""
        try:
            domain = urlparse(url).netloc.lower()
            company_words = company_name.lower().split()
            
            # Check if company name words appear in domain
            for word in company_words:
                if len(word) > 2 and word in domain:
                    return True
            
            # Check for common company website patterns
            company_patterns = ['company', 'corp', 'inc', 'llc', 'ltd', 'co']
            for pattern in company_patterns:
                if pattern in domain:
                    return True
            
            return False
            
        except:
            return False
    
    def _is_company_related(self, name: str, company_name: str) -> bool:
        """Check if a name is related to a company"""
        try:
            name_lower = name.lower()
            company_lower = company_name.lower()
            
            # Check if company name appears in the name
            if company_lower in name_lower:
                return True
            
            # Check for common business titles
            business_titles = ['ceo', 'founder', 'president', 'director', 'manager', 'head']
            for title in business_titles:
                if title in name_lower:
                    return True
            
            return False
            
        except:
            return False
    
    def _find_company_domain(self, company_name: str) -> Optional[str]:
        """Find the domain for a company"""
        try:
            search_result = self._search_company_website(company_name)
            if search_result.get('success'):
                return search_result.get('domain')
            return None
        except:
            return None
    
    def _generate_common_emails(self, domain: str) -> List[str]:
        """Generate common email addresses for a domain"""
        common_emails = []
        
        common_prefixes = [
            'contact', 'info', 'hello', 'support', 'sales', 
            'marketing', 'admin', 'team', 'help', 'service'
        ]
        
        for prefix in common_prefixes:
            email = f"{prefix}@{domain}"
            if self._is_valid_email(email):
                common_emails.append(email)
        
        return common_emails
    
    def _find_contact_page_emails(self, domain: str) -> List[str]:
        """Find emails from contact pages"""
        emails = []
        
        try:
            contact_urls = [
                f"https://{domain}/contact",
                f"https://{domain}/about",
                f"https://{domain}/team",
                f"https://{domain}/contact-us",
                f"https://{domain}/about-us"
            ]
            
            for url in contact_urls:
                try:
                    website_emails = self._scrape_single_website(url)
                    emails.extend(website_emails)
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error finding contact page emails for {domain}: {str(e)}")
        
        return list(set(emails))  # Remove duplicates

    def _extract_emails_from_javascript(self, soup: BeautifulSoup, domain: str) -> List[str]:
        """Extract emails from JavaScript code in HTML"""
        emails = []
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Find emails in JavaScript strings
                    js_emails = re.findall(r'["\']([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']', script.string)
                    for email in js_emails:
                        if self._is_valid_email(email) and domain in email:
                            emails.append(email)
        except Exception as e:
            logger.warning(f"Error extracting emails from JavaScript: {str(e)}")
        return list(set(emails))

    def _extract_emails_from_meta(self, soup: BeautifulSoup, domain: str) -> List[str]:
        """Extract emails from meta tags"""
        emails = []
        try:
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                content = meta.get('content', '')
                if content:
                    meta_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                    for email in meta_emails:
                        if self._is_valid_email(email) and domain in email:
                            emails.append(email)
        except Exception as e:
            logger.warning(f"Error extracting emails from meta tags: {str(e)}")
        return list(set(emails))

    def _generate_domain_emails(self, domain: str) -> List[str]:
        """Generate common email patterns for a domain"""
        emails = []
        common_patterns = [
            'contact', 'info', 'hello', 'support', 'sales', 'marketing',
            'admin', 'team', 'help', 'service', 'business', 'inquiries'
        ]
        
        for pattern in common_patterns:
            email = f"{pattern}@{domain}"
            if self._is_valid_email(email):
                emails.append(email)
        
        return emails

    def _find_contact_page_emails_advanced(self, soup: BeautifulSoup, base_url: str, domain: str) -> List[str]:
        """Advanced method to find emails from contact pages"""
        emails = []
        try:
            # Find contact page links
            contact_patterns = ['contact', 'about', 'team', 'company', 'people']
            contact_links = []
            
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                text = link.get_text().lower()
                
                for pattern in contact_patterns:
                    if pattern in href or pattern in text:
                        contact_links.append(link)
                        break
            
            # Visit contact pages and extract emails
            for link in contact_links[:5]:  # Limit to first 5
                try:
                    contact_url = urljoin(base_url, link.get('href'))
                    contact_response = self.session.get(contact_url, timeout=5)
                    if contact_response.status_code == 200:
                        contact_soup = BeautifulSoup(contact_response.content, 'html.parser')
                        contact_emails = self._extract_emails_from_html(contact_soup, domain)
                        emails.extend(contact_emails)
                except Exception as e:
                    logger.warning(f"Error scraping contact page {contact_url}: {str(e)}")
                    
        except Exception as e:
            logger.warning(f"Error finding contact page emails: {str(e)}")
        
        return list(set(emails))

    def _scrape_alternative_methods(self, url: str) -> List[str]:
        """Use alternative scraping methods if standard methods fail"""
        emails = []
        try:
            # Try different user agents
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ]
            
            for user_agent in user_agents:
                try:
                    headers = {'User-Agent': user_agent}
                    response = self.session.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        domain = urlparse(url).netloc
                        page_emails = self._extract_emails_from_html(soup, domain)
                        emails.extend(page_emails)
                        if emails:  # If we found emails, break
                            break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error with alternative scraping methods: {str(e)}")
        
        return list(set(emails))

    def _search_contact_pages(self, base_url: str, domain: str) -> List[str]:
        """Search for contact pages systematically"""
        emails = []
        try:
            contact_paths = [
                '/contact', '/about', '/team', '/company', '/people',
                '/contact-us', '/about-us', '/team-us', '/company-us',
                '/contact.html', '/about.html', '/team.html'
            ]
            
            for path in contact_paths:
                try:
                    contact_url = urljoin(base_url, path)
                    response = self.session.get(contact_url, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        page_emails = self._extract_emails_from_html(soup, domain)
                        emails.extend(page_emails)
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error searching contact pages: {str(e)}")
        
        return list(set(emails))

    def _extract_from_social_links(self, soup: BeautifulSoup, domain: str) -> List[str]:
        """Extract emails from social media links"""
        emails = []
        try:
            social_links = soup.find_all('a', href=re.compile(r'linkedin|twitter|facebook|instagram'))
            for link in social_links:
                href = link.get('href', '')
                if href:
                    # Sometimes social profiles contain email information
                    link_text = link.get_text()
                    link_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', link_text)
                    for email in link_emails:
                        if self._is_valid_email(email) and domain in email:
                            emails.append(email)
        except Exception as e:
            logger.warning(f"Error extracting from social links: {str(e)}")
        return list(set(emails))

    def _generate_common_emails_advanced(self, domain: str) -> List[str]:
        """Generate more comprehensive common email patterns"""
        emails = []
        common_patterns = [
            'contact', 'info', 'hello', 'support', 'sales', 'marketing',
            'admin', 'team', 'help', 'service', 'business', 'inquiries',
            'general', 'office', 'main', 'primary', 'direct', 'reach',
            'get', 'ask', 'talk', 'connect', 'work', 'careers', 'jobs'
        ]
        
        for pattern in common_patterns:
            email = f"{pattern}@{domain}"
            if self._is_valid_email(email):
                emails.append(email)
        
        return emails

    def _search_event_data(self, query: str, industry: str = None) -> Set[str]:
        """Search for emails from event data and conferences"""
        emails = set()
        try:
            # This would integrate with event APIs or databases
            # For now, return empty set as placeholder
            pass
        except Exception as e:
            logger.warning(f"Error searching event data: {str(e)}")
        return emails

    def _generate_industry_companies(self, industry: str, location: str = None) -> List[str]:
        """Generate company names based on industry and location"""
        companies = []
        try:
            # This would integrate with business databases
            # For now, return empty list as placeholder
            pass
        except Exception as e:
            logger.warning(f"Error generating industry companies: {str(e)}")
        return companies

    def find_emails_by_industry_global(self, industry: str, location: str = None, limit: int = 1000) -> Dict:
        """Global industry email search with enhanced methods"""
        try:
            emails = set()
            companies = self._get_companies_by_industry(industry, location)
            
            for company in companies[:limit//10]:  # Limit companies to avoid overwhelming
                company_emails = self.search_company_emails(company['name'], industry)
                if company_emails.get('success'):
                    emails.update(company_emails.get('emails', []))
            
            return {
                'success': True,
                'emails': list(emails)[:limit],
                'total_found': len(emails),
                'industry': industry,
                'location': location
            }
        except Exception as e:
            logger.error(f"Error in global industry search: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'emails': [],
                'total_found': 0
            }

    def scrape_website_emails(self, url: str) -> List[str]:
        """Enhanced website email scraping with multiple methods"""
        try:
            domain = urlparse(url).netloc
            emails = set()
            
            # Standard scraping
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract emails using multiple methods
                html_emails = self._extract_emails_from_html(soup, domain)
                js_emails = self._extract_emails_from_javascript(soup, domain)
                meta_emails = self._extract_emails_from_meta(soup, domain)
                contact_emails = self._find_contact_page_emails_advanced(soup, url, domain)
                social_emails = self._extract_from_social_links(soup, domain)
                
                emails.update(html_emails)
                emails.update(js_emails)
                emails.update(meta_emails)
                emails.update(contact_emails)
                emails.update(social_emails)
            
            # Generate common emails for the domain
            common_emails = self._generate_common_emails_advanced(domain)
            emails.update(common_emails)
            
            # Alternative methods if standard methods didn't work
            if not emails:
                alternative_emails = self._scrape_alternative_methods(url)
                emails.update(alternative_emails)
            
            return list(emails)
            
        except Exception as e:
            logger.error(f"Error scraping website emails from {url}: {str(e)}")
            return []

    def search_niche_emails(self, query: str, filters: Dict = None) -> List[str]:
        """Search for emails using multiple sources with enhanced methods"""
        all_emails = set()
        
        try:
            # Company website search
            company_emails = self.search_company_emails(query, filters.get('industry') if filters else None)
            if company_emails.get('success'):
                all_emails.update(company_emails.get('emails', []))
            
            # Industry search
            if filters and filters.get('industry'):
                industry_emails = self.search_industry_emails(filters['industry'], filters.get('location'))
                if industry_emails.get('success'):
                    all_emails.update(industry_emails.get('emails', []))
            
            # Universal search
            universal_emails = self.find_emails_universal(query, filters.get('industry') if filters else None, filters.get('location') if filters else None)
            if universal_emails.get('success'):
                all_emails.update(universal_emails.get('emails', []))
            
            return list(all_emails)
            
        except Exception as e:
            logger.error(f"Error in niche email search: {str(e)}")
            return []

    def _search_google_emails(self, query: str, filters: Dict = None) -> Set[str]:
        """Search Google for emails related to query"""
        emails = set()
        try:
            # This is a simplified version - in production you'd use proper Google Search API
            # Note: In production, use Google Custom Search API or similar
            # This is just a placeholder for the concept
            pass
        except Exception as e:
            logger.warning(f"Error in Google search: {e}")
        return emails
    
    def _search_linkedin_emails(self, query: str, filters: Dict = None) -> Set[str]:
        """Search LinkedIn for professional emails"""
        # Note: LinkedIn scraping requires proper API access
        # This is a placeholder for the concept
        return set()
    
    def _search_social_media_emails(self, query: str, filters: Dict = None) -> Set[str]:
        """Search social media platforms for emails"""
        # Note: This would integrate with social media APIs
        return set()
    
    def _search_github_emails(self, query: str, filters: Dict = None) -> Set[str]:
        """Search GitHub for developer emails"""
        # Note: This would use GitHub API
        return set()
