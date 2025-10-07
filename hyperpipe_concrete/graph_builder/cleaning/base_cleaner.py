from hyperpipe_core import Step
import dateparser
from price_parser import Price
import re

class Cleaner(Step):
    
    def __init__(
        self,
        name: str = "BaseCleaner",
        remove_punctuation: bool = True,
        normalize_case: bool = True
    ):
        super().__init__()
        self.name = name
        self.remove_punctuation = remove_punctuation
        self.normalize_case = normalize_case


    def _detect_date_entity(self, entity) -> bool:
        try:
            parsed_date = dateparser.parse(entity.name, settings={'STRICT_PARSING': False})
            if parsed_date:
                return True
        except Exception as e:
            pass
        
        return False
    
    def _detect_price_entity(self, entity) -> bool:
        try:
            parsed_price = Price.fromstring(entity.name)
            if parsed_price.amount is not None:
                return True
        except Exception as e:
            pass
        
        # Also detect percentage values and other numeric formats
        import re
        text = entity.name.strip()
        
        # Check for percentage patterns like "2%", "15.5%", "100%"
        if re.match(r'^\d+(\.\d+)?%$', text):
            return True
        
        # Check for currency patterns like "$100", "€50", "£25.50"
        if re.match(r'^[€$£¥]\d+(\.\d+)?$', text):
            return True
        
        # Check for numeric values with units like "2.5M", "1B", "500K"
        if re.match(r'^\d+(\.\d+)?[KMB]?$', text):
            return True
        
        return False

    def _detect_and_mark_special_types(self, entity) -> None:
        if self._detect_date_entity(entity):
            entity.special_type = 'DATE'
        elif self._detect_price_entity(entity):
            entity.special_type = 'PRICE'

    def _clean_text(self, text: str) -> str:
        if not text:
            return text
        
        # Basic cleaning - remove extra whitespace
        cleaned_text = text.strip()
        
        # Remove problematic characters that might cause issues
        cleaned_text = re.sub(r'[{}[\]()]', '', cleaned_text)
        
        # Remove extra punctuation if requested
        if self.remove_punctuation:
            # Keep only alphanumeric, spaces, and basic punctuation
            cleaned_text = re.sub(r'[^\w\s\-\.]', ' ', cleaned_text)
        
        # Normalize case if requested
        if self.normalize_case:
            cleaned_text = cleaned_text.lower()
        
        # Clean up multiple spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # If cleaning resulted in empty text, return original
        if not cleaned_text:
            return text.strip()
        
        return cleaned_text

    def _clean_entity(self, entity) -> None:
        self._detect_and_mark_special_types(entity)
        
        # For special types (DATE, PRICE), preserve original format
        if entity.special_type in ['DATE', 'PRICE']:
            # Only do basic whitespace cleaning for special types
            entity.name = entity.name.strip()
            entity.label = entity.label.strip()
            return
        
        # Store original name for fallback
        original_name = entity.name
        
        # Clean the entity name
        cleaned_name = self._clean_text(entity.name)
        
        # Only use cleaned name if it's not empty and not too different from original
        if cleaned_name and len(cleaned_name) >= len(original_name) * 0.3:
            entity.name = cleaned_name
        else:
            # Fallback to basic cleaning
            entity.name = original_name.strip()
        
        # Clean label
        original_label = entity.label
        cleaned_label = self._clean_text(entity.label)
        
        if cleaned_label and len(cleaned_label) >= len(original_label) * 0.3:
            entity.label = cleaned_label
        else:
            entity.label = original_label.strip()
