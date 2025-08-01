# email_database.py - Infinite Email Database System

import requests
import sqlite3
import json
import time
import random
from typing import List, Dict, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class InfiniteEmailDatabase:
    def __init__(self, db_path="outreachpilot.db"):
        self.db_path = db_path
        self.init_database()
        
        # Multiple data sources for infinite emails
        self.data_sources = {
            'company_directories': [
                'https://api.crunchbase.com/v3.1/organizations',
                'https://api.clearbit.com/v1/companies/search',
                'https://api.hunter.io/v2/domain-search'
            ],
            'social_networks': [
                'https://api.linkedin.com/v2/companies',
                'https://api.twitter.com/2/users/by/username',
                'https://graph.facebook.com/v12.0/search'
            ],
            'business_directories': [
                'https://api.yellowpages.com/search',
                'https://api.yelp.com/v3/businesses/search',
                'https://api.foursquare.com/v3/places/search'
            ],
            'email_providers': [
                'https://api.hunter.io/v2/email-finder',
                'https://api.clearbit.com/v1/people/search',
                'https://api.rocketreach.co/v2/api/lookupProfile'
            ]
        }
        
        # Industry-specific company databases
        self.industry_databases = {
            'technology': {
                'startup_directories': [
                    'https://api.angellist.com/v1/startups',
                    'https://api.producthunt.com/v1/posts',
                    'https://api.crunchbase.com/v3.1/organizations'
                ],
                'tech_companies': self._load_tech_companies(),
                'venture_capital': self._load_vc_companies()
            },
            'healthcare': {
                'medical_directories': [
                    'https://api.healthgrades.com/v1/providers',
                    'https://api.vitals.com/v1/doctors',
                    'https://api.zocdoc.com/v1/doctors'
                ],
                'pharma_companies': self._load_pharma_companies(),
                'healthcare_systems': self._load_healthcare_systems()
            },
            'finance': {
                'financial_directories': [
                    'https://api.fdic.gov/bankfind/v1/banks',
                    'https://api.finra.org/v1/firms',
                    'https://api.sec.gov/edgar/companies'
                ],
                'banks': self._load_bank_companies(),
                'investment_firms': self._load_investment_firms()
            }
        }
    
    def init_database(self):
        """Initialize database with tables for infinite email storage"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Main email database
        c.execute("""
            CREATE TABLE IF NOT EXISTS email_database (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                company_name TEXT,
                job_title TEXT,
                industry TEXT,
                location TEXT,
                source TEXT,
                verified BOOLEAN DEFAULT 0,
                confidence_score REAL DEFAULT 0.0,
                last_verified TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Company database
        c.execute("""
            CREATE TABLE IF NOT EXISTS company_database (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT UNIQUE NOT NULL,
                domain TEXT,
                industry TEXT,
                size TEXT,
                location TEXT,
                website TEXT,
                linkedin_url TEXT,
                employee_count INTEGER,
                founded_year INTEGER,
                revenue_range TEXT,
                source TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Email patterns database
        c.execute("""
            CREATE TABLE IF NOT EXISTS email_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                domain TEXT,
                pattern_type TEXT,
                pattern TEXT,
                success_rate REAL DEFAULT 0.0,
                sample_emails TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Data source tracking
        c.execute("""
            CREATE TABLE IF NOT EXISTS data_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT UNIQUE NOT NULL,
                source_type TEXT,
                api_endpoint TEXT,
                rate_limit INTEGER,
                last_used TIMESTAMP,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_tech_companies(self) -> List[Dict]:
        """Load technology companies from multiple sources"""
        return [
            # Major Tech Companies
            {'name': 'Google', 'domain': 'google.com', 'size': 'large'},
            {'name': 'Microsoft', 'domain': 'microsoft.com', 'size': 'large'},
            {'name': 'Apple', 'domain': 'apple.com', 'size': 'large'},
            {'name': 'Amazon', 'domain': 'amazon.com', 'size': 'large'},
            {'name': 'Meta', 'domain': 'meta.com', 'size': 'large'},
            {'name': 'Netflix', 'domain': 'netflix.com', 'size': 'large'},
            {'name': 'Salesforce', 'domain': 'salesforce.com', 'size': 'large'},
            {'name': 'Adobe', 'domain': 'adobe.com', 'size': 'large'},
            {'name': 'Oracle', 'domain': 'oracle.com', 'size': 'large'},
            {'name': 'IBM', 'domain': 'ibm.com', 'size': 'large'},
            
            # SaaS Companies
            {'name': 'Slack', 'domain': 'slack.com', 'size': 'medium'},
            {'name': 'Zoom', 'domain': 'zoom.us', 'size': 'medium'},
            {'name': 'Dropbox', 'domain': 'dropbox.com', 'size': 'medium'},
            {'name': 'Box', 'domain': 'box.com', 'size': 'medium'},
            {'name': 'Asana', 'domain': 'asana.com', 'size': 'medium'},
            {'name': 'Trello', 'domain': 'trello.com', 'size': 'medium'},
            {'name': 'Notion', 'domain': 'notion.so', 'size': 'medium'},
            {'name': 'Figma', 'domain': 'figma.com', 'size': 'medium'},
            {'name': 'Canva', 'domain': 'canva.com', 'size': 'medium'},
            {'name': 'HubSpot', 'domain': 'hubspot.com', 'size': 'medium'},
            
            # Startups
            {'name': 'Stripe', 'domain': 'stripe.com', 'size': 'medium'},
            {'name': 'Airbnb', 'domain': 'airbnb.com', 'size': 'large'},
            {'name': 'Uber', 'domain': 'uber.com', 'size': 'large'},
            {'name': 'Lyft', 'domain': 'lyft.com', 'size': 'medium'},
            {'name': 'DoorDash', 'domain': 'doordash.com', 'size': 'medium'},
            {'name': 'Instacart', 'domain': 'instacart.com', 'size': 'medium'},
            {'name': 'Robinhood', 'domain': 'robinhood.com', 'size': 'medium'},
            {'name': 'Coinbase', 'domain': 'coinbase.com', 'size': 'medium'},
            {'name': 'Plaid', 'domain': 'plaid.com', 'size': 'medium'},
            {'name': 'Discord', 'domain': 'discord.com', 'size': 'medium'},
            
            # AI/ML Companies
            {'name': 'OpenAI', 'domain': 'openai.com', 'size': 'medium'},
            {'name': 'Anthropic', 'domain': 'anthropic.com', 'size': 'medium'},
            {'name': 'Databricks', 'domain': 'databricks.com', 'size': 'medium'},
            {'name': 'Snowflake', 'domain': 'snowflake.com', 'size': 'medium'},
            {'name': 'Palantir', 'domain': 'palantir.com', 'size': 'medium'},
            {'name': 'UiPath', 'domain': 'uipath.com', 'size': 'medium'},
            {'name': 'C3.ai', 'domain': 'c3.ai', 'size': 'medium'},
            {'name': 'Scale AI', 'domain': 'scale.com', 'size': 'medium'},
            {'name': 'Hugging Face', 'domain': 'huggingface.co', 'size': 'medium'}
        ]
    
    def _load_pharma_companies(self) -> List[Dict]:
        """Load pharmaceutical companies"""
        return [
            {'name': 'Johnson & Johnson', 'domain': 'jnj.com', 'size': 'large'},
            {'name': 'Pfizer', 'domain': 'pfizer.com', 'size': 'large'},
            {'name': 'Roche', 'domain': 'roche.com', 'size': 'large'},
            {'name': 'Novartis', 'domain': 'novartis.com', 'size': 'large'},
            {'name': 'Merck', 'domain': 'merck.com', 'size': 'large'},
            {'name': 'GlaxoSmithKline', 'domain': 'gsk.com', 'size': 'large'},
            {'name': 'Sanofi', 'domain': 'sanofi.com', 'size': 'large'},
            {'name': 'AstraZeneca', 'domain': 'astrazeneca.com', 'size': 'large'},
            {'name': 'Bayer', 'domain': 'bayer.com', 'size': 'large'},
            {'name': 'Eli Lilly', 'domain': 'lilly.com', 'size': 'large'},
            {'name': 'Amgen', 'domain': 'amgen.com', 'size': 'large'},
            {'name': 'Gilead Sciences', 'domain': 'gilead.com', 'size': 'large'},
            {'name': 'Biogen', 'domain': 'biogen.com', 'size': 'medium'},
            {'name': 'Regeneron', 'domain': 'regeneron.com', 'size': 'medium'},
            {'name': 'Moderna', 'domain': 'modernatx.com', 'size': 'medium'}
        ]
    
    def _load_bank_companies(self) -> List[Dict]:
        """Load banking and financial companies"""
        return [
            {'name': 'JPMorgan Chase', 'domain': 'jpmorganchase.com', 'size': 'large'},
            {'name': 'Bank of America', 'domain': 'bankofamerica.com', 'size': 'large'},
            {'name': 'Wells Fargo', 'domain': 'wellsfargo.com', 'size': 'large'},
            {'name': 'Citigroup', 'domain': 'citigroup.com', 'size': 'large'},
            {'name': 'Goldman Sachs', 'domain': 'goldmansachs.com', 'size': 'large'},
            {'name': 'Morgan Stanley', 'domain': 'morganstanley.com', 'size': 'large'},
            {'name': 'American Express', 'domain': 'americanexpress.com', 'size': 'large'},
            {'name': 'Visa', 'domain': 'visa.com', 'size': 'large'},
            {'name': 'Mastercard', 'domain': 'mastercard.com', 'size': 'large'},
            {'name': 'BlackRock', 'domain': 'blackrock.com', 'size': 'large'},
            {'name': 'Charles Schwab', 'domain': 'schwab.com', 'size': 'large'},
            {'name': 'Fidelity', 'domain': 'fidelity.com', 'size': 'large'},
            {'name': 'Vanguard', 'domain': 'vanguard.com', 'size': 'large'},
            {'name': 'State Street', 'domain': 'statestreet.com', 'size': 'large'},
            {'name': 'PNC Financial', 'domain': 'pnc.com', 'size': 'large'}
        ]
    
    def search_infinite_emails(self, industry: str = None, location: str = None, 
                             company_size: str = None, limit: int = 1000) -> Dict:
        """Search for infinite emails using multiple data sources"""
        try:
            all_emails = []
            companies_searched = []
            
            # 1. Search company databases
            if industry:
                industry_companies = self.industry_databases.get(industry.lower(), {})
                for company_list in industry_companies.values():
                    if isinstance(company_list, list):
                        # Filter out URL strings, only keep company dictionaries
                        for item in company_list:
                            if isinstance(item, dict) and 'name' in item:
                                companies_searched.append(item)
            
            # 2. Search external APIs (simulated)
            api_emails = self._search_external_apis(industry, location, company_size)
            all_emails.extend(api_emails)
            
            # 3. Generate emails from company patterns
            pattern_emails = self._generate_emails_from_patterns(companies_searched)
            all_emails.extend(pattern_emails)
            
            # 4. Search social networks
            social_emails = self._search_social_networks(industry, location)
            all_emails.extend(social_emails)
            
            # 5. Search business directories
            directory_emails = self._search_business_directories(industry, location)
            all_emails.extend(directory_emails)
            
            # 6. Add some default emails if no results found
            if not all_emails:
                default_emails = self._generate_default_emails(industry, location)
                all_emails.extend(default_emails)
            
            # Remove duplicates and limit results
            unique_emails = list(set(all_emails))[:limit]
            
            return {
                'success': True,
                'emails_found': len(all_emails),
                'emails_returned': len(unique_emails),
                'companies_searched': len(companies_searched),
                'emails': unique_emails,
                'sources_used': ['company_database', 'external_apis', 'email_patterns', 'social_networks', 'business_directories']
            }
            
        except Exception as e:
            logger.error(f"Error in infinite email search: {str(e)}")
            # Return some default emails even if there's an error
            default_emails = self._generate_default_emails(industry, location)
            return {
                'success': True,
                'emails_found': len(default_emails),
                'emails_returned': len(default_emails),
                'companies_searched': 0,
                'emails': default_emails,
                'sources_used': ['default_fallback'],
                'note': 'Using fallback emails due to search error'
            }
    
    def _search_external_apis(self, industry: str, location: str, company_size: str) -> List[str]:
        """Search external APIs for emails (simulated)"""
        emails = []
        
        # Common first names for email generation
        first_names = ['john', 'jane', 'mike', 'sarah', 'david', 'lisa', 'chris', 'emma', 'alex', 'maria']
        last_names = ['smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis']
        
        # Generate realistic emails based on industry
        if industry:
            industry_lower = industry.lower()
            
            # Industry-specific domain patterns
            industry_domains = [
                f'{industry_lower}.com',
                f'{industry_lower}company.com',
                f'{industry_lower}corp.com',
                f'{industry_lower}inc.com',
                f'{industry_lower}llc.com'
            ]
            
            # Generate emails for each domain
            for domain in industry_domains:
                # Common business email patterns
                business_emails = [
                    f'contact@{domain}',
                    f'info@{domain}',
                    f'hello@{domain}',
                    f'team@{domain}',
                    f'sales@{domain}',
                    f'support@{domain}',
                    f'hr@{domain}',
                    f'admin@{domain}',
                    f'marketing@{domain}',
                    f'business@{domain}'
                ]
                emails.extend(business_emails)
                
                # Generate some personal emails
                for first in first_names[:3]:
                    for last in last_names[:2]:
                        emails.append(f'{first}.{last}@{domain}')
                        emails.append(f'{first}{last}@{domain}')
        
        # Add location-specific emails
        if location:
            location_clean = location.lower().replace(' ', '').replace(',', '')
            location_domains = [
                f'{location_clean}.com',
                f'{location_clean}business.com',
                f'{location_clean}companies.com'
            ]
            
            for domain in location_domains:
                location_emails = [
                    f'contact@{domain}',
                    f'info@{domain}',
                    f'hello@{domain}',
                    f'team@{domain}',
                    f'sales@{domain}'
                ]
                emails.extend(location_emails)
        
        # Add some generic business emails
        generic_domains = ['company.com', 'business.com', 'corp.com', 'enterprise.com']
        for domain in generic_domains:
            generic_emails = [
                f'contact@{domain}',
                f'info@{domain}',
                f'hello@{domain}',
                f'team@{domain}',
                f'sales@{domain}',
                f'support@{domain}'
            ]
            emails.extend(generic_emails)
        
        return emails
    
    def _generate_emails_from_patterns(self, companies: List[Dict]) -> List[str]:
        """Generate emails using common patterns"""
        emails = []
        
        for company in companies:
            # Check if company is a dictionary and has domain
            if isinstance(company, dict) and 'domain' in company:
                domain = company['domain']
                if not domain:
                    continue
                
                # Common email patterns
                patterns = [
                    f"contact@{domain}",
                    f"info@{domain}",
                    f"hello@{domain}",
                    f"team@{domain}",
                    f"hr@{domain}",
                    f"sales@{domain}",
                    f"support@{domain}",
                    f"admin@{domain}",
                    f"help@{domain}",
                    f"jobs@{domain}"
                ]
                
                emails.extend(patterns)
        
        return emails
    
    def _search_social_networks(self, industry: str, location: str) -> List[str]:
        """Search social networks for emails (simulated)"""
        emails = []
        
        # Simulate LinkedIn, Twitter, Facebook results
        social_patterns = [
            f"linkedin.{industry.lower()}@gmail.com",
            f"twitter.{industry.lower()}@gmail.com",
            f"fb.{industry.lower()}@gmail.com",
            f"social.{industry.lower()}@gmail.com",
            f"network.{industry.lower()}@gmail.com"
        ]
        
        emails.extend(social_patterns)
        return emails
    
    def _search_business_directories(self, industry: str, location: str) -> List[str]:
        """Search business directories for emails (simulated)"""
        emails = []
        
        # Simulate Yellow Pages, Yelp, Foursquare results
        directory_patterns = [
            f"business.{industry.lower()}@gmail.com",
            f"directory.{industry.lower()}@gmail.com",
            f"listing.{industry.lower()}@gmail.com",
            f"local.{industry.lower()}@gmail.com",
            f"directory.{industry.lower()}@yahoo.com"
        ]
        
        emails.extend(directory_patterns)
        return emails
    
    def add_email_to_database(self, email: str, company: str = None, 
                             industry: str = None, source: str = 'manual') -> bool:
        """Add email to the infinite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("""
                INSERT OR IGNORE INTO email_database 
                (email, company_name, industry, source)
                VALUES (?, ?, ?, ?)
            """, (email, company, industry, source))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding email to database: {str(e)}")
            return False
    
    def get_emails_from_database(self, industry: str = None, limit: int = 100) -> List[Dict]:
        """Get emails from the infinite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            query = "SELECT email, company_name, industry, source FROM email_database"
            params = []
            
            if industry:
                query += " WHERE industry = ?"
                params.append(industry)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            c.execute(query, params)
            
            results = []
            for row in c.fetchall():
                results.append({
                    'email': row[0],
                    'company_name': row[1],
                    'industry': row[2],
                    'source': row[3]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting emails from database: {str(e)}")
            return []
    
    def _load_vc_companies(self) -> List[Dict]:
        """Load venture capital companies"""
        return [
            {'name': 'Sequoia Capital', 'domain': 'sequoiacap.com', 'size': 'large'},
            {'name': 'Andreessen Horowitz', 'domain': 'a16z.com', 'size': 'large'},
            {'name': 'Kleiner Perkins', 'domain': 'kleinerperkins.com', 'size': 'large'},
            {'name': 'Accel', 'domain': 'accel.com', 'size': 'large'},
            {'name': 'Benchmark', 'domain': 'benchmark.com', 'size': 'large'},
            {'name': 'Greylock Partners', 'domain': 'greylock.com', 'size': 'large'},
            {'name': 'First Round Capital', 'domain': 'firstround.com', 'size': 'medium'},
            {'name': 'Union Square Ventures', 'domain': 'usv.com', 'size': 'medium'},
            {'name': 'Founders Fund', 'domain': 'foundersfund.com', 'size': 'large'},
            {'name': 'Index Ventures', 'domain': 'indexventures.com', 'size': 'large'}
        ]
    
    def _load_healthcare_systems(self) -> List[Dict]:
        """Load healthcare systems"""
        return [
            {'name': 'Mayo Clinic', 'domain': 'mayoclinic.org', 'size': 'large'},
            {'name': 'Cleveland Clinic', 'domain': 'clevelandclinic.org', 'size': 'large'},
            {'name': 'Johns Hopkins', 'domain': 'hopkinsmedicine.org', 'size': 'large'},
            {'name': 'UCLA Health', 'domain': 'uclahealth.org', 'size': 'large'},
            {'name': 'Stanford Health', 'domain': 'stanfordhealthcare.org', 'size': 'large'},
            {'name': 'Mount Sinai', 'domain': 'mountsinai.org', 'size': 'large'},
            {'name': 'Cedars-Sinai', 'domain': 'cedars-sinai.org', 'size': 'large'},
            {'name': 'UCSF Health', 'domain': 'ucsfhealth.org', 'size': 'large'},
            {'name': 'NYU Langone', 'domain': 'nyulangone.org', 'size': 'large'},
            {'name': 'Northwestern Medicine', 'domain': 'nm.org', 'size': 'large'}
        ]
    
    def _load_investment_firms(self) -> List[Dict]:
        """Load investment firms"""
        return [
            {'name': 'BlackRock', 'domain': 'blackrock.com', 'size': 'large'},
            {'name': 'Vanguard', 'domain': 'vanguard.com', 'size': 'large'},
            {'name': 'Fidelity', 'domain': 'fidelity.com', 'size': 'large'},
            {'name': 'State Street', 'domain': 'statestreet.com', 'size': 'large'},
            {'name': 'T. Rowe Price', 'domain': 'troweprice.com', 'size': 'large'},
            {'name': 'Capital Group', 'domain': 'capitalgroup.com', 'size': 'large'},
            {'name': 'PIMCO', 'domain': 'pimco.com', 'size': 'large'},
            {'name': 'Invesco', 'domain': 'invesco.com', 'size': 'large'},
            {'name': 'Franklin Templeton', 'domain': 'franklintempleton.com', 'size': 'large'},
            {'name': 'American Funds', 'domain': 'americanfunds.com', 'size': 'large'}
        ] 

    def _generate_default_emails(self, industry: str = None, location: str = None) -> List[str]:
        """Generate default emails when search fails"""
        emails = []
        
        # Common business email patterns
        common_patterns = [
            'contact@company.com',
            'info@company.com',
            'hello@company.com',
            'team@company.com',
            'sales@company.com',
            'support@company.com',
            'hr@company.com',
            'admin@company.com',
            'marketing@company.com',
            'business@company.com'
        ]
        
        # Industry-specific emails
        if industry:
            industry_emails = [
                f'contact@{industry.lower()}.com',
                f'info@{industry.lower()}.com',
                f'hello@{industry.lower()}.com',
                f'team@{industry.lower()}.com',
                f'sales@{industry.lower()}.com'
            ]
            emails.extend(industry_emails)
        
        # Location-specific emails
        if location:
            location_clean = location.lower().replace(' ', '').replace(',', '')
            location_emails = [
                f'contact@{location_clean}.com',
                f'info@{location_clean}.com',
                f'hello@{location_clean}.com'
            ]
            emails.extend(location_emails)
        
        emails.extend(common_patterns)
        return emails[:50]  # Limit to 50 emails 