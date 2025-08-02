# email_scraper.py - Comprehensive email scraping system

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailScraper:
    def __init__(self, redis_url="redis://localhost:6379"):
        try:
            self.redis_client = redis.from_url(redis_url)
        except:
            # If Redis is not available, use a simple in-memory cache
            self.redis_client = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Email patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b')
        
        # Rate limiting
        self.rate_limits = {
            'requests_per_minute': 30,
            'requests_per_hour': 1000,
            'delay_between_requests': 2
        }
        
        # Common email patterns for different companies
        self.common_patterns = {
            'firstname.lastname': lambda f, l: f"{f.lower()}.{l.lower()}",
            'firstname_lastname': lambda f, l: f"{f.lower()}_{l.lower()}",
            'firstname': lambda f, l: f"{f.lower()}",
            'firstinitiallastname': lambda f, l: f"{f[0].lower()}{l.lower()}",
            'firstnamelastname': lambda f, l: f"{f.lower()}{l.lower()}"
        }
    
    def scrape_website(self, url: str, max_depth: int = 2) -> Dict:
        """Scrape emails from a website"""
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
            
            # Start scraping
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
    
    def _scrape_page_recursive(self, url: str, domain: str, emails: Set, names: Set, 
                             scraped_pages: Set, max_depth: int, current_depth: int = 0):
        """Recursively scrape pages for emails and names"""
        if current_depth > max_depth or url in scraped_pages:
            return
        
        try:
            scraped_pages.add(url)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract emails from text content
            text_content = soup.get_text()
            found_emails = self.email_pattern.findall(text_content)
            emails.update([email.lower() for email in found_emails if email.lower().endswith(domain)])
            
            # Extract names from text content
            found_names = self.name_pattern.findall(text_content)
            names.update(found_names)
            
            # Extract emails from href attributes
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('mailto:'):
                    email = href[7:]  # Remove 'mailto:'
                    if email.lower().endswith(domain):
                        emails.add(email.lower())
            
            # Find more pages to scrape
            if current_depth < max_depth:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    # Only follow links within the same domain
                    if urlparse(full_url).netloc == domain:
                        self._scrape_page_recursive(full_url, domain, emails, names, 
                                                  scraped_pages, max_depth, current_depth + 1)
            
        except Exception as e:
            logger.warning(f"Error scraping page {url}: {str(e)}")
    
    def _generate_potential_emails(self, names: Set, domain: str) -> List[str]:
        """Generate potential emails based on common patterns"""
        potential_emails = []
        
        for name in names:
            parts = name.split()
            if len(parts) >= 2:
                first_name, last_name = parts[0], parts[1]
                
                for pattern_name, pattern_func in self.common_patterns.items():
                    try:
                        email = f"{pattern_func(first_name, last_name)}@{domain}"
                        potential_emails.append(email)
                    except:
                        continue
        
        return list(set(potential_emails))
    
    def _verify_emails(self, emails: List[str]) -> List[str]:
        """Verify emails using DNS MX record check"""
        verified_emails = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_email = {executor.submit(self._verify_single_email, email): email 
                             for email in emails}
            
            for future in concurrent.futures.as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    if future.result():
                        verified_emails.append(email)
                except Exception as e:
                    logger.warning(f"Error verifying {email}: {str(e)}")
        
        return verified_emails
    
    def _verify_single_email(self, email: str) -> bool:
        """Verify a single email by checking MX records"""
        try:
            domain = email.split('@')[1]
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except:
            return False
    
    def _check_rate_limits(self):
        """Check and enforce rate limits"""
        if not self.redis_client:
            # Skip rate limiting if Redis is not available
            return
            
        try:
            current_time = time.time()
            
            # Check minute rate limit
            minute_key = f"rate_limit:minute:{int(current_time / 60)}"
            minute_count = self.redis_client.incr(minute_key)
            self.redis_client.expire(minute_key, 60)
            
            if minute_count > self.rate_limits['requests_per_minute']:
                sleep_time = 60 - (current_time % 60)
                time.sleep(sleep_time)
            
            # Check hour rate limit
            hour_key = f"rate_limit:hour:{int(current_time / 3600)}"
            hour_count = self.redis_client.incr(hour_key)
            self.redis_client.expire(hour_key, 3600)
            
            if hour_count > self.rate_limits['requests_per_hour']:
                raise Exception("Hourly rate limit exceeded")
            
            # Add delay between requests
            time.sleep(self.rate_limits['delay_between_requests'])
        except Exception as e:
            logger.warning(f"Rate limiting disabled: {str(e)}")
            # Continue without rate limiting if Redis is not available
            pass
    
    def search_company_emails(self, company_name: str, industry: str = None) -> Dict:
        """Search for company emails using multiple sources"""
        try:
            # Check rate limits
            self._check_rate_limits()
            
            all_emails = set()
            sources = []
            
            # Search company website
            website_emails = self._search_company_website(company_name)
            if website_emails['success']:
                all_emails.update(website_emails['emails'])
                sources.append({
                    'source': 'company_website',
                    'emails': website_emails['emails'],
                    'count': len(website_emails['emails'])
                })
            
            # Search LinkedIn (simulated - would need LinkedIn API in production)
            linkedin_emails = self._search_linkedin(company_name)
            if linkedin_emails['success']:
                all_emails.update(linkedin_emails['emails'])
                sources.append({
                    'source': 'linkedin',
                    'emails': linkedin_emails['emails'],
                    'count': len(linkedin_emails['emails'])
                })
            
            # Search industry databases
            if industry:
                industry_emails = self._search_industry_database(company_name, industry)
                if industry_emails['success']:
                    all_emails.update(industry_emails['emails'])
                    sources.append({
                        'source': 'industry_database',
                        'emails': industry_emails['emails'],
                        'count': len(industry_emails['emails'])
                    })
            
            # Verify all found emails
            verified_emails = self._verify_emails(list(all_emails))
            
            return {
                'success': True,
                'company': company_name,
                'industry': industry,
                'total_emails_found': len(all_emails),
                'total_emails_verified': len(verified_emails),
                'sources': sources,
                'emails': verified_emails
            }
            
        except Exception as e:
            logger.error(f"Error searching emails for {company_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'company': company_name
            }

    def search_industry_emails(self, industry: str, location: str = None, company_size: str = None) -> Dict:
        """Search for emails from companies in a specific industry"""
        try:
            # Check rate limits
            self._check_rate_limits()
            
            # Get companies in the industry
            companies = self._get_companies_by_industry(industry, location, company_size)
            
            all_emails = []
            company_results = []
            
            for company in companies:
                company_result = self.search_company_emails(company['name'], industry)
                if company_result['success']:
                    all_emails.extend(company_result['emails'])
                    company_results.append({
                        'company': company['name'],
                        'emails_found': len(company_result['emails']),
                        'emails': company_result['emails']
                    })
            
            # Remove duplicates and verify
            unique_emails = list(set(all_emails))
            verified_emails = self._verify_emails(unique_emails)
            
            return {
                'success': True,
                'industry': industry,
                'location': location,
                'company_size': company_size,
                'companies_searched': len(companies),
                'emails_found': len(all_emails),
                'emails_verified': len(verified_emails),
                'emails': verified_emails,
                'company_results': company_results
            }
            
        except Exception as e:
            logger.error(f"Error searching industry emails: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'industry': industry,
                'location': location,
                'company_size': company_size
            }

    def _get_companies_by_industry(self, industry: str, location: str = None, company_size: str = None) -> List[Dict]:
        """Get list of companies in a specific industry"""
        # This would typically connect to a business database API
        # For now, we'll simulate with some common companies by industry
        
        industry_companies = {
            'technology': [
                {'name': 'Google', 'website': 'google.com'},
                {'name': 'Microsoft', 'website': 'microsoft.com'},
                {'name': 'Apple', 'website': 'apple.com'},
                {'name': 'Amazon', 'website': 'amazon.com'},
                {'name': 'Meta', 'website': 'meta.com'},
                {'name': 'Netflix', 'website': 'netflix.com'},
                {'name': 'Salesforce', 'website': 'salesforce.com'},
                {'name': 'Adobe', 'website': 'adobe.com'},
                {'name': 'Oracle', 'website': 'oracle.com'},
                {'name': 'IBM', 'website': 'ibm.com'}
            ],
            'healthcare': [
                {'name': 'Johnson & Johnson', 'website': 'jnj.com'},
                {'name': 'Pfizer', 'website': 'pfizer.com'},
                {'name': 'UnitedHealth Group', 'website': 'unitedhealthgroup.com'},
                {'name': 'Anthem', 'website': 'anthem.com'},
                {'name': 'Cigna', 'website': 'cigna.com'},
                {'name': 'CVS Health', 'website': 'cvshealth.com'},
                {'name': 'Walgreens', 'website': 'walgreens.com'},
                {'name': 'McKesson', 'website': 'mckesson.com'},
                {'name': 'AmerisourceBergen', 'website': 'amerisourcebergen.com'},
                {'name': 'Cardinal Health', 'website': 'cardinalhealth.com'}
            ],
            'finance': [
                {'name': 'JPMorgan Chase', 'website': 'jpmorganchase.com'},
                {'name': 'Bank of America', 'website': 'bankofamerica.com'},
                {'name': 'Wells Fargo', 'website': 'wellsfargo.com'},
                {'name': 'Citigroup', 'website': 'citigroup.com'},
                {'name': 'Goldman Sachs', 'website': 'goldmansachs.com'},
                {'name': 'Morgan Stanley', 'website': 'morganstanley.com'},
                {'name': 'American Express', 'website': 'americanexpress.com'},
                {'name': 'Visa', 'website': 'visa.com'},
                {'name': 'Mastercard', 'website': 'mastercard.com'},
                {'name': 'BlackRock', 'website': 'blackrock.com'}
            ],
            'retail': [
                {'name': 'Walmart', 'website': 'walmart.com'},
                {'name': 'Target', 'website': 'target.com'},
                {'name': 'Home Depot', 'website': 'homedepot.com'},
                {'name': 'Costco', 'website': 'costco.com'},
                {'name': 'Lowe\'s', 'website': 'lowes.com'},
                {'name': 'Best Buy', 'website': 'bestbuy.com'},
                {'name': 'Macy\'s', 'website': 'macys.com'},
                {'name': 'Kohl\'s', 'website': 'kohls.com'},
                {'name': 'Nordstrom', 'website': 'nordstrom.com'},
                {'name': 'Starbucks', 'website': 'starbucks.com'}
            ],
            'manufacturing': [
                {'name': 'General Electric', 'website': 'ge.com'},
                {'name': 'Boeing', 'website': 'boeing.com'},
                {'name': 'Ford', 'website': 'ford.com'},
                {'name': 'General Motors', 'website': 'gm.com'},
                {'name': 'Toyota', 'website': 'toyota.com'},
                {'name': 'Honda', 'website': 'honda.com'},
                {'name': 'Tesla', 'website': 'tesla.com'},
                {'name': 'Caterpillar', 'website': 'cat.com'},
                {'name': '3M', 'website': '3m.com'},
                {'name': 'Procter & Gamble', 'website': 'pg.com'}
            ]
        }
        
        companies = industry_companies.get(industry.lower(), [])
        
        # Filter by location and company size if specified
        if location:
            # In a real implementation, you'd filter by location
            pass
        
        if company_size:
            # In a real implementation, you'd filter by company size
            pass
        
        return companies
    
    def _search_company_website(self, company_name: str) -> Dict:
        """Search for company website and scrape emails"""
        try:
            # Try common domain patterns
            domain_patterns = [
                f"{company_name.lower().replace(' ', '')}.com",
                f"{company_name.lower().replace(' ', '-')}.com",
                f"{company_name.lower().replace(' ', '')}.net",
                f"{company_name.lower().replace(' ', '')}.org"
            ]
            
            for domain in domain_patterns:
                try:
                    result = self.scrape_website(f"https://{domain}")
                    if result['success'] and result['emails']:
                        return result
                except:
                    continue
            
            return {'success': False, 'emails': []}
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'emails': []}
    
    def _search_linkedin(self, company_name: str) -> Dict:
        """Search LinkedIn for company emails (simulated)"""
        # In production, this would use LinkedIn API
        # For now, return simulated results
        return {
            'success': True,
            'emails': [
                f"hr@{company_name.lower().replace(' ', '')}.com",
                f"info@{company_name.lower().replace(' ', '')}.com",
                f"contact@{company_name.lower().replace(' ', '')}.com"
            ]
        }
    
    def _search_industry_database(self, company_name: str, industry: str) -> Dict:
        """Search industry-specific databases"""
        # In production, this would connect to various industry databases
        # For now, return simulated results
        return {
            'success': True,
            'emails': [
                f"sales@{company_name.lower().replace(' ', '')}.com",
                f"marketing@{company_name.lower().replace(' ', '')}.com"
            ]
        }
    
    def save_scraped_emails(self, user_id: int, company_name: str, emails: List[str], 
                          source: str = 'manual') -> bool:
        """Save scraped emails to database"""
        try:
            conn = sqlite3.connect("outreachpilot.db")
            c = conn.cursor()
            
            # Create scraped_emails table if it doesn't exist
            c.execute("""
                CREATE TABLE IF NOT EXISTS scraped_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    company_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    source TEXT DEFAULT 'manual',
                    verified BOOLEAN DEFAULT 1,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Insert emails
            for email in emails:
                c.execute("""
                    INSERT OR IGNORE INTO scraped_emails 
                    (user_id, company_name, email, source, verified)
                    VALUES (?, ?, ?, ?, 1)
                """, (user_id, company_name, email, source))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving scraped emails: {str(e)}")
            return False
    
    def get_user_scraped_emails(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get user's scraped emails"""
        try:
            conn = sqlite3.connect("outreachpilot.db")
            c = conn.cursor()
            
            c.execute("""
                SELECT company_name, email, source, scraped_at
                FROM scraped_emails 
                WHERE user_id = ?
                ORDER BY scraped_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            results = []
            for row in c.fetchall():
                results.append({
                    'company_name': row[0],
                    'email': row[1],
                    'source': row[2],
                    'scraped_at': row[3]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting user scraped emails: {str(e)}")
            return []

    def scrape_website_emails(self, url: str) -> List[str]:
        """Scrape emails from a website with enhanced capabilities"""
        print(f"Scraping website: {url}")
        
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Enhanced headers to bypass basic firewalls
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            # Make request with timeout and retry
            session = requests.Session()
            session.headers.update(headers)
            
            try:
                response = session.get(url, timeout=10, allow_redirects=True)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                # Try alternative methods
                return self._scrape_alternative_methods(url)
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract domain for email generation
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Method 1: Find emails in HTML content
            emails = self._extract_emails_from_html(soup, domain)
            
            # Method 2: Find emails in JavaScript
            js_emails = self._extract_emails_from_javascript(soup, domain)
            emails.extend(js_emails)
            
            # Method 3: Find emails in meta tags
            meta_emails = self._extract_emails_from_meta(soup, domain)
            emails.extend(meta_emails)
            
            # Method 4: Generate emails based on domain patterns
            generated_emails = self._generate_domain_emails(domain)
            emails.extend(generated_emails)
            
            # Method 5: Look for contact forms and pages
            contact_emails = self._find_contact_page_emails(soup, url, domain)
            emails.extend(contact_emails)
            
            # Remove duplicates and validate
            unique_emails = list(set(emails))
            valid_emails = [email for email in unique_emails if self._is_valid_email(email)]
            
            print(f"Found {len(valid_emails)} valid emails from {url}")
            return valid_emails
            
        except Exception as e:
            print(f"Error scraping website {url}: {e}")
            return []
    
    def _extract_emails_from_html(self, soup: BeautifulSoup, domain: str) -> List[str]:
        """Extract emails from HTML content"""
        emails = []
        
        # Find all text content
        text_content = soup.get_text()
        
        # Use regex to find email patterns
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+@' + domain.replace('.', r'\.') + r'\b',
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]*' + domain.split('.')[-1] + r'\b'
        ]
        
        for pattern in email_patterns:
            found_emails = re.findall(pattern, text_content, re.IGNORECASE)
            emails.extend(found_emails)
        
        # Find emails in href attributes
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'mailto:' in href:
                email = href.replace('mailto:', '').split('?')[0]
                emails.append(email)
        
        return emails
    
    def _extract_emails_from_javascript(self, soup: BeautifulSoup, domain: str) -> List[str]:
        """Extract emails from JavaScript code"""
        emails = []
        
        # Find script tags
        for script in soup.find_all('script'):
            if script.string:
                script_content = script.string
                
                # Look for email patterns in JavaScript
                email_patterns = [
                    r'["\']([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})["\']',
                    r'["\']([A-Za-z0-9._%+-]+@' + domain.replace('.', r'\.') + r')["\']'
                ]
                
                for pattern in email_patterns:
                    found_emails = re.findall(pattern, script_content, re.IGNORECASE)
                    emails.extend(found_emails)
        
        return emails
    
    def _extract_emails_from_meta(self, soup: BeautifulSoup, domain: str) -> List[str]:
        """Extract emails from meta tags"""
        emails = []
        
        # Check meta tags for contact information
        meta_tags = [
            'contact',
            'email',
            'support',
            'sales',
            'info'
        ]
        
        for meta in soup.find_all('meta'):
            content = meta.get('content', '')
            if any(tag in content.lower() for tag in meta_tags):
                # Look for email in content
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                if email_match:
                    emails.append(email_match.group())
        
        return emails
    
    def _generate_domain_emails(self, domain: str) -> List[str]:
        """Generate common email patterns for the domain"""
        emails = []
        
        # Common email patterns
        patterns = [
            'info', 'contact', 'hello', 'team', 'sales', 'support', 'admin',
            'hr', 'marketing', 'business', 'office', 'general', 'help',
            'get', 'start', 'hello', 'contact', 'info'
        ]
        
        # Generate emails for the domain
        for pattern in patterns:
            emails.append(f'{pattern}@{domain}')
        
        # Generate emails for subdomains
        subdomains = ['www', 'mail', 'email', 'contact', 'support']
        for subdomain in subdomains:
            for pattern in patterns[:5]:  # Use first 5 patterns for subdomains
                emails.append(f'{pattern}@{subdomain}.{domain}')
        
        return emails
    
    def _find_contact_page_emails(self, soup: BeautifulSoup, base_url: str, domain: str) -> List[str]:
        """Find emails from contact pages"""
        emails = []
        
        # Look for contact page links
        contact_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            link_text = link.get_text().lower()
            
            # Check if it's a contact page
            if any(word in href or word in link_text for word in ['contact', 'about', 'team', 'support']):
                contact_links.append(link['href'])
        
        # Visit contact pages (limit to 3 to avoid too many requests)
        for i, link in enumerate(contact_links[:3]):
            try:
                if link.startswith('/'):
                    contact_url = base_url + link
                elif link.startswith('http'):
                    contact_url = link
                else:
                    contact_url = base_url + '/' + link
                
                # Make request to contact page
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                response = session.get(contact_url, timeout=5)
                if response.status_code == 200:
                    contact_soup = BeautifulSoup(response.content, 'html.parser')
                    contact_emails = self._extract_emails_from_html(contact_soup, domain)
                    emails.extend(contact_emails)
                    
            except Exception as e:
                print(f"Error accessing contact page {link}: {e}")
                continue
        
        return emails
    
    def _scrape_alternative_methods(self, url: str) -> List[str]:
        """Try alternative scraping methods when direct access fails"""
        emails = []
        
        try:
            # Method 1: Try with different User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                domain = urlparse(url).netloc
                emails = self._extract_emails_from_html(soup, domain)
                emails.extend(self._generate_domain_emails(domain))
        
        except Exception as e:
            print(f"Alternative method failed: {e}")
        
        return emails
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return bool(re.match(pattern, email))

# Flask routes for email scraping
def add_scraper_routes(app):
    """Add email scraping routes to Flask app"""
    
    @app.route('/api/scrape/website', methods=['POST'])
    def scrape_website_api():
        """API endpoint to scrape emails from a website"""
        print("Website scraping API called")
        
        try:
            data = request.get_json()
            print(f"Request data: {data}")
            
            url = data.get('url')
            user_id = session.get('user', {}).get('id')
            
            print(f"URL: {url}, User ID: {user_id}")
            
            if not url:
                print("No URL provided")
                return jsonify({'success': False, 'error': 'URL is required'})
            
            if not user_id:
                print("User not authenticated")
                return jsonify({'success': False, 'error': 'User not authenticated'})
            
            # Check subscription limits
            from subscription_manager import SubscriptionManager
            sub_mgr = SubscriptionManager()
            limit_check = sub_mgr.check_limit(user_id, 'scrapes')
            
            print(f"Limit check: {limit_check}")
            
            if not limit_check['allowed']:
                return jsonify({
                    'success': False, 
                    'error': f'Scraping limit reached ({limit_check["current"]}/{limit_check["limit"]})'
                })
            
            # Perform enhanced scraping
            print("Starting enhanced scraping...")
            scraper = EmailScraper()
            
            # Use the new enhanced scraping method
            emails = scraper.scrape_website_emails(url)
            
            # Create result format
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            result = {
                'success': True,
                'emails': emails,
                'domain': domain,
                'url': url,
                'emails_found': len(emails)
            }
            
            print(f"Scraping result: {result}")
            
            if result['success']:
                # Save emails to database
                scraper.save_scraped_emails(user_id, result['domain'], result['emails'], 'website')
                
                # Increment usage
                sub_mgr.increment_usage(user_id, 'scrapes')
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Error in website scraping: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scrape/industry', methods=['POST'])
    def search_industry_emails_api():
        """API endpoint to search for industry emails"""
        try:
            data = request.get_json()
            industry = data.get('industry')
            location = data.get('location')
            company_size = data.get('company_size')
            user_id = session.get('user', {}).get('id')
            
            if not industry:
                return jsonify({'success': False, 'error': 'Industry is required'})
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User not authenticated'})
            
            # Check subscription limits
            from subscription_manager import SubscriptionManager
            sub_mgr = SubscriptionManager()
            limit_check = sub_mgr.check_limit(user_id, 'scrapes')
            
            if not limit_check['allowed']:
                return jsonify({
                    'success': False, 
                    'error': f'Scraping limit reached ({limit_check["current"]}/{limit_check["limit"]})'
                })
            
            # Perform industry search
            scraper = EmailScraper()
            result = scraper.search_industry_emails(industry, location, company_size)
            
            if result['success']:
                # Save emails to database
                for company_result in result.get('company_results', []):
                    scraper.save_scraped_emails(
                        user_id, 
                        company_result['company'], 
                        company_result['emails'], 
                        'industry_search'
                    )
                
                # Increment usage
                sub_mgr.increment_usage(user_id, 'scrapes')
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scrape/company', methods=['POST'])
    def search_company_emails_api():
        """API endpoint to search for company emails"""
        try:
            data = request.get_json()
            company_name = data.get('company_name')
            industry = data.get('industry')
            user_id = session.get('user', {}).get('id')
            
            if not company_name:
                return jsonify({'success': False, 'error': 'Company name is required'})
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User not authenticated'})
            
            # Check subscription limits
            from subscription_manager import SubscriptionManager
            sub_mgr = SubscriptionManager()
            limit_check = sub_mgr.check_limit(user_id, 'scrapes')
            
            if not limit_check['allowed']:
                return jsonify({
                    'success': False, 
                    'error': f'Scraping limit reached ({limit_check["current"]}/{limit_check["limit"]})'
                })
            
            # Perform search
            scraper = EmailScraper()
            result = scraper.search_company_emails(company_name, industry)
            
            if result['success']:
                # Save emails to database
                scraper.save_scraped_emails(user_id, company_name, result['emails'], 'company_search')
                
                # Increment usage
                sub_mgr.increment_usage(user_id, 'scrapes')
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scraped-emails', methods=['GET'])
    def get_scraped_emails_api():
        """API endpoint to get user's scraped emails"""
        try:
            user_id = session.get('user', {}).get('id')
            limit = request.args.get('limit', 100, type=int)
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User not authenticated'})
            
            scraper = EmailScraper()
            emails = scraper.get_user_scraped_emails(user_id, limit)
            
            return jsonify({
                'success': True,
                'emails': emails,
                'count': len(emails)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

# Import Flask dependencies
from flask import request, jsonify, session
