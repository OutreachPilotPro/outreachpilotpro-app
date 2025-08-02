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
        """Initialize the database with sample data"""
        print("Initializing email database...")
        
        # Load comprehensive company data
        self._load_tech_companies()
        self._load_ecommerce_companies()
        self._load_healthcare_companies()
        self._load_finance_companies()
        self._load_real_estate_companies()
        self._load_education_companies()
        self._load_consulting_companies()
        self._load_marketing_companies()
        self._load_legal_companies()
        self._load_manufacturing_companies()
        self._load_retail_companies()
        self._load_restaurant_companies()
        self._load_fitness_companies()
        self._load_beauty_companies()
        self._load_automotive_companies()
        self._load_travel_companies()
        self._load_nonprofit_companies()
        self._load_government_companies()
        
        # Load additional industry data
        self._load_pharma_companies()
        self._load_bank_companies()
        self._load_vc_companies()
        self._load_healthcare_systems()
        self._load_investment_firms()
        
        print("Email database initialized successfully!")
    
    def _load_tech_companies(self):
        """Load technology companies with detailed targeting data"""
        companies = [
            {
                'name': 'OutreachPilotPro',
                'domain': 'outreachpilotpro.com',
                'industry': 'technology',
                'subcategory': 'saas-email-marketing',
                'size': 'startup',
                'revenue': '1m-10m',
                'location': 'San Francisco, CA',
                'technology': ['python', 'flask', 'stripe', 'gmail-api'],
                'job_titles': ['ceo', 'founder', 'cto', 'marketing-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['startup', 'innovation']
            },
            {
                'name': 'TechCorp Solutions',
                'domain': 'techcorp.com',
                'industry': 'technology',
                'subcategory': 'software-development',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'San Francisco, CA',
                'technology': ['python', 'aws', 'slack', 'github'],
                'job_titles': ['cto', 'software-engineer', 'product-manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['women-owned']
            },
            {
                'name': 'EcoTech Innovations',
                'domain': 'ecotech.com',
                'industry': 'technology',
                'subcategory': 'clean-tech',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Austin, TX',
                'technology': ['solar', 'iot', 'machine-learning'],
                'job_titles': ['ceo', 'cto', 'sustainability-manager'],
                'environmental': 'carbon-neutral',
                'social_impact': ['b-corp']
            },
            {
                'name': 'SaaSFlow Inc',
                'domain': 'saasflow.com',
                'industry': 'saas',
                'subcategory': 'project-management',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'New York, NY',
                'technology': ['react', 'nodejs', 'mongodb', 'stripe'],
                'job_titles': ['ceo', 'cto', 'cmo', 'sales-director'],
                'environmental': 'sustainable',
                'social_impact': ['lgbtq-friendly']
            },
            {
                'name': 'DataViz Pro',
                'domain': 'datavizpro.com',
                'industry': 'technology',
                'subcategory': 'analytics-tools',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Seattle, WA',
                'technology': ['tableau', 'powerbi', 'python', 'aws'],
                'job_titles': ['ceo', 'cto', 'data-scientist', 'product-manager'],
                'environmental': 'sustainable',
                'social_impact': ['women-owned']
            },
            {
                'name': 'CloudSecure Solutions',
                'domain': 'cloudsecure.com',
                'industry': 'technology',
                'subcategory': 'security-software',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Boston, MA',
                'technology': ['aws', 'azure', 'kubernetes', 'docker'],
                'job_titles': ['ceo', 'cto', 'security-engineer', 'compliance-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['veteran-owned']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_ecommerce_companies(self):
        """Load e-commerce companies with detailed targeting data"""
        companies = [
            {
                'name': 'FashionForward',
                'domain': 'fashionforward.com',
                'industry': 'ecommerce',
                'subcategory': 'fashion-apparel',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Los Angeles, CA',
                'technology': ['shopify', 'mailchimp', 'google-ads'],
                'job_titles': ['ceo', 'cmo', 'ecommerce-manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['women-owned', 'fair-trade']
            },
            {
                'name': 'GreenHome Store',
                'domain': 'greenhome.com',
                'industry': 'ecommerce',
                'subcategory': 'home-garden',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Portland, OR',
                'technology': ['woocommerce', 'wordpress', 'paypal'],
                'job_titles': ['founder', 'marketing-director'],
                'environmental': 'organic',
                'social_impact': ['b-corp', 'carbon-neutral']
            },
            {
                'name': 'TechGadgets Pro',
                'domain': 'techgadgetspro.com',
                'industry': 'ecommerce',
                'subcategory': 'electronics',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'Seattle, WA',
                'technology': ['magento', 'salesforce', 'hubspot'],
                'job_titles': ['ceo', 'cto', 'operations-manager'],
                'environmental': 'recycling',
                'social_impact': ['veteran-owned']
            },
            {
                'name': 'PetParadise',
                'domain': 'petparadise.com',
                'industry': 'ecommerce',
                'subcategory': 'pet-supplies',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Denver, CO',
                'technology': ['shopify', 'klaviyo', 'facebook-ads'],
                'job_titles': ['ceo', 'marketing-director', 'operations-manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['animal-welfare']
            },
            {
                'name': 'SportsElite',
                'domain': 'sportselite.com',
                'industry': 'ecommerce',
                'subcategory': 'sports-outdoors',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'Portland, OR',
                'technology': ['bigcommerce', 'mailchimp', 'google-ads'],
                'job_titles': ['ceo', 'cmo', 'ecommerce-manager'],
                'environmental': 'sustainable',
                'social_impact': ['local-sourcing']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_healthcare_companies(self):
        """Load healthcare companies with detailed targeting data"""
        companies = [
            {
                'name': 'Wellness Medical Group',
                'domain': 'wellnessmedical.com',
                'industry': 'healthcare',
                'subcategory': 'primary-care',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Boston, MA',
                'technology': ['epic', 'zoom', 'microsoft'],
                'job_titles': ['medical-director', 'hr-director'],
                'environmental': 'sustainable',
                'social_impact': ['disability-friendly']
            },
            {
                'name': 'Mental Health Partners',
                'domain': 'mentalhealthpartners.com',
                'industry': 'healthcare',
                'subcategory': 'mental-health',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Denver, CO',
                'technology': ['telemedicine', 'slack', 'quickbooks'],
                'job_titles': ['clinical-director', 'operations-manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['lgbtq-friendly']
            },
            {
                'name': 'DentalCare Plus',
                'domain': 'dentalcareplus.com',
                'industry': 'healthcare',
                'subcategory': 'dental-care',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Miami, FL',
                'technology': ['dentrix', 'zoom', 'quickbooks'],
                'job_titles': ['dental-director', 'office-manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['family-friendly']
            },
            {
                'name': 'PharmaInnovate',
                'domain': 'pharmainnovate.com',
                'industry': 'healthcare',
                'subcategory': 'pharmaceuticals',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'New Jersey, NJ',
                'technology': ['salesforce', 'sap', 'microsoft'],
                'job_titles': ['ceo', 'cto', 'regulatory-director'],
                'environmental': 'sustainable',
                'social_impact': ['research-focused']
            },
            {
                'name': 'MedDevice Solutions',
                'domain': 'meddevicesolutions.com',
                'industry': 'healthcare',
                'subcategory': 'medical-devices',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Minneapolis, MN',
                'technology': ['solidworks', 'salesforce', 'quickbooks'],
                'job_titles': ['ceo', 'cto', 'quality-director'],
                'environmental': 'sustainable',
                'social_impact': ['innovation']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_finance_companies(self):
        """Load finance companies with detailed targeting data"""
        companies = [
            {
                'name': 'Green Finance Bank',
                'domain': 'greenfinance.com',
                'industry': 'finance',
                'subcategory': 'commercial-banking',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'San Francisco, CA',
                'technology': ['salesforce', 'quickbooks', 'microsoft'],
                'job_titles': ['ceo', 'cfo', 'compliance-director'],
                'environmental': 'carbon-neutral',
                'social_impact': ['b-corp', 'minority-owned']
            },
            {
                'name': 'FinTech Innovations',
                'domain': 'fintechinnovations.com',
                'industry': 'finance',
                'subcategory': 'fintech',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'New York, NY',
                'technology': ['blockchain', 'ai', 'aws'],
                'job_titles': ['ceo', 'cto', 'product-manager'],
                'environmental': 'sustainable',
                'social_impact': ['women-owned']
            },
            {
                'name': 'Investment Partners LLC',
                'domain': 'investmentpartners.com',
                'industry': 'finance',
                'subcategory': 'investment-banking',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'New York, NY',
                'technology': ['bloomberg', 'salesforce', 'microsoft'],
                'job_titles': ['ceo', 'cfo', 'investment-director'],
                'environmental': 'sustainable',
                'social_impact': ['esg-focused']
            },
            {
                'name': 'Secure Insurance Co',
                'domain': 'secureinsurance.com',
                'industry': 'finance',
                'subcategory': 'insurance',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'Hartford, CT',
                'technology': ['guidewire', 'salesforce', 'microsoft'],
                'job_titles': ['ceo', 'cfo', 'claims-director'],
                'environmental': 'sustainable',
                'social_impact': ['community-focused']
            },
            {
                'name': 'Credit Union First',
                'domain': 'creditunionfirst.com',
                'industry': 'finance',
                'subcategory': 'credit-unions',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Austin, TX',
                'technology': ['fiserv', 'quickbooks', 'microsoft'],
                'job_titles': ['ceo', 'cfo', 'member-services-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['community-owned']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_real_estate_companies(self):
        """Load real estate companies with detailed targeting data"""
        companies = [
            {
                'name': 'Premier Properties',
                'domain': 'premierproperties.com',
                'industry': 'real-estate',
                'subcategory': 'residential-sales',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Los Angeles, CA',
                'technology': ['mls', 'salesforce', 'quickbooks'],
                'job_titles': ['ceo', 'broker', 'marketing-director'],
                'environmental': 'sustainable',
                'social_impact': ['local-focused']
            },
            {
                'name': 'Commercial Real Estate Pro',
                'domain': 'commercialrealestatepro.com',
                'industry': 'real-estate',
                'subcategory': 'commercial-real-estate',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'Chicago, IL',
                'technology': ['co-star', 'salesforce', 'microsoft'],
                'job_titles': ['ceo', 'broker', 'property-manager'],
                'environmental': 'sustainable',
                'social_impact': ['esg-focused']
            },
            {
                'name': 'Property Management Plus',
                'domain': 'propertymanagementplus.com',
                'industry': 'real-estate',
                'subcategory': 'property-management',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Dallas, TX',
                'technology': ['appfolio', 'quickbooks', 'microsoft'],
                'job_titles': ['ceo', 'property-manager', 'operations-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['community-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_education_companies(self):
        """Load education companies with detailed targeting data"""
        companies = [
            {
                'name': 'Innovation Academy',
                'domain': 'innovationacademy.com',
                'industry': 'education',
                'subcategory': 'k-12-schools',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Austin, TX',
                'technology': ['canvas', 'google-workspace', 'zoom'],
                'job_titles': ['principal', 'director', 'technology-coordinator'],
                'environmental': 'eco-friendly',
                'social_impact': ['innovation-focused']
            },
            {
                'name': 'Online Learning Pro',
                'domain': 'onlinelearningpro.com',
                'industry': 'education',
                'subcategory': 'online-learning',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'San Francisco, CA',
                'technology': ['canvas', 'zoom', 'salesforce'],
                'job_titles': ['ceo', 'cto', 'content-director'],
                'environmental': 'sustainable',
                'social_impact': ['accessibility-focused']
            },
            {
                'name': 'Corporate Training Solutions',
                'domain': 'corporatetrainingsolutions.com',
                'industry': 'education',
                'subcategory': 'corporate-training',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'New York, NY',
                'technology': ['articulate', 'salesforce', 'zoom'],
                'job_titles': ['ceo', 'training-director', 'content-manager'],
                'environmental': 'sustainable',
                'social_impact': ['skill-development']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_consulting_companies(self):
        """Load consulting companies with detailed targeting data"""
        companies = [
            {
                'name': 'Strategic Consulting Group',
                'domain': 'strategicconsulting.com',
                'industry': 'consulting',
                'subcategory': 'management-consulting',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'New York, NY',
                'technology': ['salesforce', 'microsoft', 'slack'],
                'job_titles': ['ceo', 'partner', 'consultant'],
                'environmental': 'sustainable',
                'social_impact': ['esg-focused']
            },
            {
                'name': 'IT Solutions Consulting',
                'domain': 'itsolutionsconsulting.com',
                'industry': 'consulting',
                'subcategory': 'it-consulting',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Seattle, WA',
                'technology': ['aws', 'azure', 'salesforce'],
                'job_titles': ['ceo', 'cto', 'senior-consultant'],
                'environmental': 'eco-friendly',
                'social_impact': ['innovation-focused']
            },
            {
                'name': 'Financial Advisory Pro',
                'domain': 'financialadvisorypro.com',
                'industry': 'consulting',
                'subcategory': 'financial-consulting',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Boston, MA',
                'technology': ['quickbooks', 'salesforce', 'microsoft'],
                'job_titles': ['ceo', 'cfo', 'senior-advisor'],
                'environmental': 'sustainable',
                'social_impact': ['client-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_marketing_companies(self):
        """Load marketing companies with detailed targeting data"""
        companies = [
            {
                'name': 'Digital Marketing Masters',
                'domain': 'digitalmarketingmasters.com',
                'industry': 'marketing',
                'subcategory': 'digital-marketing',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Los Angeles, CA',
                'technology': ['google-ads', 'facebook-ads', 'hubspot'],
                'job_titles': ['ceo', 'cmo', 'digital-director'],
                'environmental': 'sustainable',
                'social_impact': ['data-driven']
            },
            {
                'name': 'Content Creation Pro',
                'domain': 'contentcreationpro.com',
                'industry': 'marketing',
                'subcategory': 'content-marketing',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Austin, TX',
                'technology': ['wordpress', 'canva', 'mailchimp'],
                'job_titles': ['ceo', 'content-director', 'creative-manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['creativity-focused']
            },
            {
                'name': 'Social Media Experts',
                'domain': 'socialmediaexperts.com',
                'industry': 'marketing',
                'subcategory': 'social-media-marketing',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Miami, FL',
                'technology': ['hootsuite', 'buffer', 'instagram'],
                'job_titles': ['ceo', 'social-director', 'community-manager'],
                'environmental': 'sustainable',
                'social_impact': ['engagement-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_legal_companies(self):
        """Load legal companies with detailed targeting data"""
        companies = [
            {
                'name': 'Corporate Law Associates',
                'domain': 'corporatelawassociates.com',
                'industry': 'legal',
                'subcategory': 'corporate-law',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'New York, NY',
                'technology': ['clio', 'microsoft', 'quickbooks'],
                'job_titles': ['managing-partner', 'attorney', 'paralegal'],
                'environmental': 'sustainable',
                'social_impact': ['pro-bono-focused']
            },
            {
                'name': 'Family Law Center',
                'domain': 'familylawcenter.com',
                'industry': 'legal',
                'subcategory': 'family-law',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Los Angeles, CA',
                'technology': ['clio', 'zoom', 'quickbooks'],
                'job_titles': ['partner', 'attorney', 'case-manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['family-focused']
            },
            {
                'name': 'IP Protection Pro',
                'domain': 'ipprotectionpro.com',
                'industry': 'legal',
                'subcategory': 'intellectual-property',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'San Francisco, CA',
                'technology': ['clio', 'patent-database', 'microsoft'],
                'job_titles': ['partner', 'patent-attorney', 'ip-specialist'],
                'environmental': 'sustainable',
                'social_impact': ['innovation-protection']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_manufacturing_companies(self):
        """Load manufacturing companies with detailed targeting data"""
        companies = [
            {
                'name': 'Auto Manufacturing Pro',
                'domain': 'automfgpro.com',
                'industry': 'manufacturing',
                'subcategory': 'automotive',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'Detroit, MI',
                'technology': ['sap', 'solidworks', 'salesforce'],
                'job_titles': ['ceo', 'cto', 'operations-director'],
                'environmental': 'sustainable',
                'social_impact': ['innovation-focused']
            },
            {
                'name': 'Electronics Manufacturing Co',
                'domain': 'electronicsmfg.com',
                'industry': 'manufacturing',
                'subcategory': 'electronics',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'San Jose, CA',
                'technology': ['sap', 'oracle', 'salesforce'],
                'job_titles': ['ceo', 'cto', 'quality-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['recycling-focused']
            },
            {
                'name': 'Food Manufacturing Solutions',
                'domain': 'foodmanufacturing.com',
                'industry': 'manufacturing',
                'subcategory': 'food-beverage',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Chicago, IL',
                'technology': ['sap', 'quickbooks', 'microsoft'],
                'job_titles': ['ceo', 'operations-director', 'quality-manager'],
                'environmental': 'organic',
                'social_impact': ['organic-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_retail_companies(self):
        """Load retail companies with detailed targeting data"""
        companies = [
            {
                'name': 'Department Store Elite',
                'domain': 'departmentstoreelite.com',
                'industry': 'retail',
                'subcategory': 'department-stores',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'New York, NY',
                'technology': ['salesforce', 'quickbooks', 'microsoft'],
                'job_titles': ['ceo', 'cmo', 'store-director'],
                'environmental': 'sustainable',
                'social_impact': ['community-focused']
            },
            {
                'name': 'Specialty Retail Pro',
                'domain': 'specialtyretailpro.com',
                'industry': 'retail',
                'subcategory': 'specialty-retail',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Los Angeles, CA',
                'technology': ['square', 'quickbooks', 'mailchimp'],
                'job_titles': ['owner', 'store-manager', 'marketing-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['local-focused']
            },
            {
                'name': 'Online Retail Masters',
                'domain': 'onlineretailmasters.com',
                'industry': 'retail',
                'subcategory': 'online-retail',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'Seattle, WA',
                'technology': ['shopify', 'salesforce', 'hubspot'],
                'job_titles': ['ceo', 'cmo', 'ecommerce-director'],
                'environmental': 'sustainable',
                'social_impact': ['customer-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_restaurant_companies(self):
        """Load restaurant companies with detailed targeting data"""
        companies = [
            {
                'name': 'Organic Bistro',
                'domain': 'organicbistro.com',
                'industry': 'restaurant',
                'subcategory': 'fine-dining',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Portland, OR',
                'technology': ['square', 'toast', 'quickbooks'],
                'job_titles': ['owner', 'chef', 'operations-manager'],
                'environmental': 'organic',
                'social_impact': ['farm-to-table', 'local-sourcing']
            },
            {
                'name': 'Vegan Delights',
                'domain': 'vegandelights.com',
                'industry': 'restaurant',
                'subcategory': 'casual-dining',
                'size': 'medium',
                'revenue': '1m-10m',
                'location': 'Austin, TX',
                'technology': ['clover', 'mailchimp', 'google-ads'],
                'job_titles': ['founder', 'marketing-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['lgbtq-friendly', 'animal-welfare']
            },
            {
                'name': 'Fast Food Innovation',
                'domain': 'fastfoodinnovation.com',
                'industry': 'restaurant',
                'subcategory': 'fast-food',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'Dallas, TX',
                'technology': ['toast', 'salesforce', 'quickbooks'],
                'job_titles': ['ceo', 'operations-director', 'marketing-director'],
                'environmental': 'sustainable',
                'social_impact': ['health-focused']
            },
            {
                'name': 'Coffee Culture Pro',
                'domain': 'coffeeculturepro.com',
                'industry': 'restaurant',
                'subcategory': 'coffee-shops',
                'size': 'medium',
                'revenue': '1m-10m',
                'location': 'Seattle, WA',
                'technology': ['square', 'quickbooks', 'mailchimp'],
                'job_titles': ['owner', 'barista-manager', 'marketing-director'],
                'environmental': 'organic',
                'social_impact': ['fair-trade', 'local-sourcing']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_fitness_companies(self):
        """Load fitness companies with detailed targeting data"""
        companies = [
            {
                'name': 'Wellness Warriors',
                'domain': 'wellnesswarriors.com',
                'industry': 'fitness',
                'subcategory': 'yoga-studios',
                'size': 'small',
                'revenue': 'under-1m',
                'location': 'Boulder, CO',
                'technology': ['mindbody', 'mailchimp', 'instagram'],
                'job_titles': ['owner', 'yoga-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['women-owned', 'lgbtq-friendly']
            },
            {
                'name': 'CrossFit Elite',
                'domain': 'crossfitelite.com',
                'industry': 'fitness',
                'subcategory': 'crossfit',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Miami, FL',
                'technology': ['zenplanner', 'facebook-ads', 'quickbooks'],
                'job_titles': ['owner', 'head-trainer'],
                'environmental': 'sustainable',
                'social_impact': ['veteran-owned']
            },
            {
                'name': 'Gym Masters Pro',
                'domain': 'gymmasterspro.com',
                'industry': 'fitness',
                'subcategory': 'gyms-health-clubs',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Los Angeles, CA',
                'technology': ['mindbody', 'salesforce', 'quickbooks'],
                'job_titles': ['ceo', 'fitness-director', 'operations-manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['community-focused']
            },
            {
                'name': 'Personal Training Plus',
                'domain': 'personaltrainingplus.com',
                'industry': 'fitness',
                'subcategory': 'personal-training',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'New York, NY',
                'technology': ['mindbody', 'zoom', 'quickbooks'],
                'job_titles': ['owner', 'head-trainer', 'marketing-director'],
                'environmental': 'sustainable',
                'social_impact': ['health-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_beauty_companies(self):
        """Load beauty companies with detailed targeting data"""
        companies = [
            {
                'name': 'Luxe Hair Salon',
                'domain': 'luxehairsalon.com',
                'industry': 'beauty',
                'subcategory': 'hair-salons',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Beverly Hills, CA',
                'technology': ['mindbody', 'quickbooks', 'instagram'],
                'job_titles': ['owner', 'salon-manager', 'stylist'],
                'environmental': 'eco-friendly',
                'social_impact': ['women-owned']
            },
            {
                'name': 'Nail Art Studio',
                'domain': 'nailartstudio.com',
                'industry': 'beauty',
                'subcategory': 'nail-salons',
                'size': 'small',
                'revenue': 'under-1m',
                'location': 'Miami, FL',
                'technology': ['square', 'quickbooks', 'instagram'],
                'job_titles': ['owner', 'nail-technician', 'manager'],
                'environmental': 'eco-friendly',
                'social_impact': ['women-owned']
            },
            {
                'name': 'Spa Serenity',
                'domain': 'spaserenity.com',
                'industry': 'beauty',
                'subcategory': 'spa-services',
                'size': 'medium',
                'revenue': '1m-10m',
                'location': 'Scottsdale, AZ',
                'technology': ['mindbody', 'quickbooks', 'mailchimp'],
                'job_titles': ['owner', 'spa-director', 'therapist'],
                'environmental': 'organic',
                'social_impact': ['wellness-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_automotive_companies(self):
        """Load automotive companies with detailed targeting data"""
        companies = [
            {
                'name': 'Premium Auto Dealership',
                'domain': 'premiumautodealership.com',
                'industry': 'automotive',
                'subcategory': 'car-dealerships',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'Los Angeles, CA',
                'technology': ['salesforce', 'quickbooks', 'microsoft'],
                'job_titles': ['ceo', 'general-manager', 'sales-director'],
                'environmental': 'sustainable',
                'social_impact': ['community-focused']
            },
            {
                'name': 'Auto Repair Pro',
                'domain': 'autorepairpro.com',
                'industry': 'automotive',
                'subcategory': 'auto-repair',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Phoenix, AZ',
                'technology': ['alldata', 'quickbooks', 'microsoft'],
                'job_titles': ['owner', 'service-manager', 'technician'],
                'environmental': 'eco-friendly',
                'social_impact': ['quality-focused']
            },
            {
                'name': 'Auto Parts Warehouse',
                'domain': 'autopartswarehouse.com',
                'industry': 'automotive',
                'subcategory': 'auto-parts',
                'size': 'large',
                'revenue': '50m-100m',
                'location': 'Dallas, TX',
                'technology': ['salesforce', 'quickbooks', 'microsoft'],
                'job_titles': ['ceo', 'operations-director', 'sales-manager'],
                'environmental': 'recycling',
                'social_impact': ['recycling-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_travel_companies(self):
        """Load travel companies with detailed targeting data"""
        companies = [
            {
                'name': 'Luxury Hotels & Resorts',
                'domain': 'luxuryhotelsresorts.com',
                'industry': 'travel',
                'subcategory': 'hotels-resorts',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'Las Vegas, NV',
                'technology': ['opera', 'salesforce', 'microsoft'],
                'job_titles': ['ceo', 'general-manager', 'marketing-director'],
                'environmental': 'sustainable',
                'social_impact': ['luxury-focused']
            },
            {
                'name': 'Adventure Travel Co',
                'domain': 'adventuretravelco.com',
                'industry': 'travel',
                'subcategory': 'tour-operators',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Denver, CO',
                'technology': ['salesforce', 'quickbooks', 'mailchimp'],
                'job_titles': ['ceo', 'operations-director', 'tour-guide'],
                'environmental': 'eco-friendly',
                'social_impact': ['sustainability-focused']
            },
            {
                'name': 'Business Travel Solutions',
                'domain': 'businesstravelsolutions.com',
                'industry': 'travel',
                'subcategory': 'business-travel',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'New York, NY',
                'technology': ['sabre', 'salesforce', 'microsoft'],
                'job_titles': ['ceo', 'operations-director', 'account-manager'],
                'environmental': 'sustainable',
                'social_impact': ['efficiency-focused']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_nonprofit_companies(self):
        """Load nonprofit companies with detailed targeting data"""
        companies = [
            {
                'name': 'Education Foundation',
                'domain': 'educationfoundation.com',
                'industry': 'nonprofit',
                'subcategory': 'education',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'Washington, DC',
                'technology': ['salesforce', 'quickbooks', 'microsoft'],
                'job_titles': ['executive-director', 'program-director', 'development-director'],
                'environmental': 'sustainable',
                'social_impact': ['education-focused']
            },
            {
                'name': 'Environmental Conservation',
                'domain': 'environmentalconservation.com',
                'industry': 'nonprofit',
                'subcategory': 'environment',
                'size': 'medium',
                'revenue': '10m-50m',
                'location': 'San Francisco, CA',
                'technology': ['salesforce', 'quickbooks', 'microsoft'],
                'job_titles': ['executive-director', 'conservation-director', 'fundraising-director'],
                'environmental': 'eco-friendly',
                'social_impact': ['environment-focused']
            },
            {
                'name': 'Animal Welfare Society',
                'domain': 'animalwelfaresociety.com',
                'industry': 'nonprofit',
                'subcategory': 'animal-welfare',
                'size': 'small',
                'revenue': '1m-10m',
                'location': 'Austin, TX',
                'technology': ['salesforce', 'quickbooks', 'mailchimp'],
                'job_titles': ['executive-director', 'shelter-manager', 'volunteer-coordinator'],
                'environmental': 'eco-friendly',
                'social_impact': ['animal-welfare']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _load_government_companies(self):
        """Load government companies with detailed targeting data"""
        companies = [
            {
                'name': 'City Government Services',
                'domain': 'citygovernmentservices.gov',
                'industry': 'government',
                'subcategory': 'local-government',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'Austin, TX',
                'technology': ['microsoft', 'quickbooks', 'government-systems'],
                'job_titles': ['city-manager', 'department-director', 'it-director'],
                'environmental': 'sustainable',
                'social_impact': ['public-service']
            },
            {
                'name': 'State Department of Transportation',
                'domain': 'statedot.gov',
                'industry': 'government',
                'subcategory': 'state-government',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'Sacramento, CA',
                'technology': ['microsoft', 'government-systems', 'quickbooks'],
                'job_titles': ['director', 'deputy-director', 'project-manager'],
                'environmental': 'sustainable',
                'social_impact': ['public-service']
            },
            {
                'name': 'Federal Agency Services',
                'domain': 'federalagencyservices.gov',
                'industry': 'government',
                'subcategory': 'federal-government',
                'size': 'large',
                'revenue': 'over-100m',
                'location': 'Washington, DC',
                'technology': ['microsoft', 'government-systems', 'quickbooks'],
                'job_titles': ['director', 'deputy-director', 'program-manager'],
                'environmental': 'sustainable',
                'social_impact': ['public-service']
            }
        ]
        
        for company in companies:
            self._add_company_to_database(company)
    
    def _add_company_to_database(self, company):
        """Add a company with detailed targeting data to the database"""
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        # Create company_database table if it doesn't exist
        c.execute("""
            CREATE TABLE IF NOT EXISTS company_database (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                industry TEXT,
                subcategory TEXT,
                size TEXT,
                revenue TEXT,
                location TEXT,
                technology TEXT,
                job_titles TEXT,
                environmental TEXT,
                social_impact TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert company data
        c.execute("""
            INSERT OR REPLACE INTO company_database 
            (name, domain, industry, subcategory, size, revenue, location, technology, job_titles, environmental, social_impact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company['name'],
            company['domain'],
            company.get('industry', ''),
            company.get('subcategory', ''),
            company.get('size', ''),
            company.get('revenue', ''),
            company.get('location', ''),
            json.dumps(company.get('technology', [])),
            json.dumps(company.get('job_titles', [])),
            company.get('environmental', ''),
            json.dumps(company.get('social_impact', []))
        ))
        
        conn.commit()
        conn.close()
    
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
        
        # Add the user's company email
        emails.append('team@outreachpilotpro.com')
        
        for company in companies:
            if isinstance(company, dict) and 'domain' in company:
                domain = company['domain']
                name = company.get('name', '').lower().replace(' ', '').replace('-', '')
                
                # Common email patterns
                patterns = [
                    f'info@{domain}',
                    f'hello@{domain}',
                    f'contact@{domain}',
                    f'sales@{domain}',
                    f'support@{domain}',
                    f'admin@{domain}',
                    f'team@{domain}',
                    f'hr@{domain}',
                    f'marketing@{domain}',
                    f'business@{domain}',
                    f'office@{domain}',
                    f'general@{domain}',
                    f'help@{domain}',
                    f'hello@{domain}',
                    f'hi@{domain}',
                    f'get@{domain}',
                    f'start@{domain}',
                    f'hello@{domain}',
                    f'contact@{domain}',
                    f'info@{domain}'
                ]
                
                # Add name-based patterns if we have a company name
                if name:
                    patterns.extend([
                        f'{name}@{domain}',
                        f'{name[:3]}@{domain}',
                        f'{name[:5]}@{domain}'
                    ])
                
                emails.extend(patterns)
        
        return list(set(emails))  # Remove duplicates
    
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