"""
Query formatter service for processing LLM responses and creating RAG queries.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class QueryFormatterService:
    """Service for formatting RAG queries from LLM responses."""
    
    def __init__(self):
        """Initialize query formatter service."""
        logger.info("Query Formatter Service initialized")
    
    def extract_regulation_info(self, extracted_text: str) -> Dict[str, Any]:
        """
        Extract country/state and ingredients/products from the LLM extracted text.
        
        Args:
            extracted_text: The text extracted from the image by the LLM
            
        Returns:
            Dictionary containing extracted information for RAG query
        """
        try:
            logger.info("Extracting regulation information from text")
            
            # Extract countries/states
            countries = self._extract_countries(extracted_text)
            states = self._extract_states(extracted_text)
            
            # Extract ingredients/products
            ingredients = self._extract_ingredients(extracted_text)
            products = self._extract_products(extracted_text)
            
            regulation_info = {
                'countries': countries,
                'states': states,
                'ingredients': ingredients,
                'products': products,
                'original_text': extracted_text
            }
            
            logger.info(f"Extracted regulation info: countries={len(countries)}, states={len(states)}, ingredients={len(ingredients)}, products={len(products)}")
            return regulation_info
            
        except Exception as e:
            logger.error(f"Error extracting regulation info: {e}")
            raise
    
    def format_rag_query(self, regulation_info: Dict[str, Any]) -> str:
        """
        Format a user query for the RAG agent based on extracted information.
        
        Args:
            regulation_info: Dictionary containing extracted countries, states, ingredients, and products
            
        Returns:
            Formatted query string for RAG agent
        """
        try:
            logger.info("Formatting RAG query from regulation info")
            
            # Determine the primary location (country or state)
            location = self._determine_primary_location(regulation_info)
            
            # Determine the primary item (ingredient or product)
            item = self._determine_primary_item(regulation_info)
            
            # Format the query
            if location and item:
                query = f"What are the rules and regulations for exporting {item} to {location}?"
            elif location:
                query = f"What are the import/export rules and regulations for {location}?"
            elif item:
                query = f"What are the rules and regulations for exporting {item}?"
            else:
                # Fallback query if we can't extract specific information
                query = "What are the general food import/export rules and regulations?"
            
            logger.info(f"Formatted RAG query: {query}")
            return query
            
        except Exception as e:
            logger.error(f"Error formatting RAG query: {e}")
            raise
    
    def _extract_countries(self, text: str) -> List[str]:
        """Extract country names from text."""
        # Common country patterns
        country_patterns = [
            r'\b(?:United States|USA|US|America)\b',
            r'\b(?:United Kingdom|UK|Britain)\b',
            r'\b(?:Canada|Canadian)\b',
            r'\b(?:Australia|Australian)\b',
            r'\b(?:Germany|German)\b',
            r'\b(?:France|French)\b',
            r'\b(?:Italy|Italian)\b',
            r'\b(?:Spain|Spanish)\b',
            r'\b(?:Japan|Japanese)\b',
            r'\b(?:China|Chinese)\b',
            r'\b(?:India|Indian)\b',
            r'\b(?:Brazil|Brazilian)\b',
            r'\b(?:Mexico|Mexican)\b',
            r'\b(?:Dubai|UAE|United Arab Emirates)\b',
            r'\b(?:Singapore|Singaporean)\b',
            r'\b(?:Netherlands|Dutch)\b',
            r'\b(?:Belgium|Belgian)\b',
            r'\b(?:Switzerland|Swiss)\b',
            r'\b(?:Sweden|Swedish)\b',
            r'\b(?:Norway|Norwegian)\b',
            r'\b(?:Denmark|Danish)\b',
        ]
        
        countries = []
        for pattern in country_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                country = match.group().strip()
                if country not in countries:
                    countries.append(country)
        
        return countries
    
    def _extract_states(self, text: str) -> List[str]:
        """Extract US state names from text."""
        # Common US state patterns
        state_patterns = [
            r'\b(?:California|CA)\b',
            r'\b(?:Texas|TX)\b',
            r'\b(?:Florida|FL)\b',
            r'\b(?:New York|NY)\b',
            r'\b(?:Illinois|IL)\b',
            r'\b(?:Pennsylvania|PA)\b',
            r'\b(?:Ohio|OH)\b',
            r'\b(?:Georgia|GA)\b',
            r'\b(?:North Carolina|NC)\b',
            r'\b(?:Michigan|MI)\b',
            r'\b(?:New Jersey|NJ)\b',
            r'\b(?:Virginia|VA)\b',
            r'\b(?:Washington|WA)\b',
            r'\b(?:Arizona|AZ)\b',
            r'\b(?:Massachusetts|MA)\b',
            r'\b(?:Tennessee|TN)\b',
            r'\b(?:Indiana|IN)\b',
            r'\b(?:Missouri|MO)\b',
            r'\b(?:Maryland|MD)\b',
            r'\b(?:Wisconsin|WI)\b',
        ]
        
        states = []
        for pattern in state_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                state = match.group().strip()
                if state not in states:
                    states.append(state)
        
        return states
    
    def _extract_ingredients(self, text: str) -> List[str]:
        """Extract ingredient names from text."""
        # Common food ingredient patterns
        ingredient_patterns = [
            r'\b(?:meat|beef|pork|chicken|poultry|lamb|fish|seafood)\b',
            r'\b(?:dairy|milk|cheese|butter|yogurt|cream)\b',
            r'\b(?:eggs|egg products)\b',
            r'\b(?:wheat|flour|grain|rice|corn|oats|barley)\b',
            r'\b(?:sugar|sweetener|honey|syrup)\b',
            r'\b(?:oil|olive oil|vegetable oil|coconut oil)\b',
            r'\b(?:salt|sodium|spices|herbs|seasoning)\b',
            r'\b(?:nuts|peanuts|almonds|walnuts|cashews)\b',
            r'\b(?:soy|soybeans|tofu)\b',
            r'\b(?:fruits|vegetables|produce)\b',
            r'\b(?:additives|preservatives|colorings|flavorings)\b',
            r'\b(?:vitamins|minerals|supplements)\b',
        ]
        
        ingredients = []
        for pattern in ingredient_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ingredient = match.group().strip()
                if ingredient not in ingredients:
                    ingredients.append(ingredient)
        
        return ingredients
    
    def _extract_products(self, text: str) -> List[str]:
        """Extract product names from text."""
        # Common food product patterns
        product_patterns = [
            r'\b(?:processed food|packaged food|canned food)\b',
            r'\b(?:beverages|drinks|juice|soda|water)\b',
            r'\b(?:snacks|chips|crackers|cookies)\b',
            r'\b(?:frozen food|ice cream)\b',
            r'\b(?:bread|bakery products)\b',
            r'\b(?:pasta|noodles)\b',
            r'\b(?:sauce|condiments|dressing)\b',
            r'\b(?:baby food|infant formula)\b',
            r'\b(?:organic food|natural products)\b',
            r'\b(?:dietary supplements|nutrition bars)\b',
        ]
        
        products = []
        for pattern in product_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                product = match.group().strip()
                if product not in products:
                    products.append(product)
        
        return products
    
    def _determine_primary_location(self, regulation_info: Dict[str, Any]) -> Optional[str]:
        """Determine the primary location from extracted information."""
        countries = regulation_info.get('countries', [])
        states = regulation_info.get('states', [])
        
        # Prioritize countries over states
        if countries:
            return countries[0]  # Take the first country found
        elif states:
            return states[0]  # Take the first state found
        
        return None
    
    def _determine_primary_item(self, regulation_info: Dict[str, Any]) -> Optional[str]:
        """Determine the primary item (ingredient or product) from extracted information."""
        ingredients = regulation_info.get('ingredients', [])
        products = regulation_info.get('products', [])
        
        # Prioritize specific ingredients over general products
        if ingredients:
            return ingredients[0]  # Take the first ingredient found
        elif products:
            return products[0]  # Take the first product found
        
        return None