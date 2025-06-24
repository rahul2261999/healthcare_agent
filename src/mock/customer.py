from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Customer:
    """Customer data model with required attributes"""
    id: str
    name: str
    phone_number: str  # Format: +1XXXXXXXXXX
    dob: str  # Format: YYYY-MM-DD


class CustomerStore:
    """Store for managing customer data with search functionality"""
    
    def __init__(self):
        self.customers: List[Customer] = []
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize store with some mock customers"""
        mock_customers = [
            Customer(
                id="CUST-1001",
                name="John Doe",
                phone_number="+14803828571",
                dob="1990-05-15"
            ),
            Customer(
                id="CUST-1002", 
                name="Jane Smith",
                phone_number="+15559876543",
                dob="1985-12-03"
            ),
            Customer(
                id="CUST-1003",
                name="Michael Johnson",
                phone_number="+15555555555",
                dob="1992-08-22"
            ),
        ]
        self.customers.extend(mock_customers)
    
    def find_customer_by_phone_number(self, phone_number: str) -> Optional[Customer]:
        """
        Find a customer by their phone number
        
        Args:
            phone_number (str): Phone number to search for (format: +1XXXXXXXXXX)
            
        Returns:
            Optional[Customer]: Customer object if found, None otherwise
        """
        for customer in self.customers:
            if customer.phone_number == phone_number:
                return customer
        return None
    
    def add_customer(self, customer: Customer) -> bool:
        """
        Add a new customer to the store
        
        Args:
            customer (Customer): Customer object to add
            
        Returns:
            bool: True if customer was added successfully, False if customer with same phone already exists
        """
        # Check if customer with same phone number already exists
        if customer.phone_number and self.find_customer_by_phone_number(
            customer.phone_number
        ):
            return False
        
        self.customers.append(customer)
        return True
    
    def get_all_customers(self) -> List[Customer]:
        """
        Get all customers in the store
        
        Returns:
            List[Customer]: List of all customers
        """
        return self.customers.copy()
    
    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """
        Find a customer by their ID
        
        Args:
            customer_id (str): Customer ID to search for
            
        Returns:
            Optional[Customer]: Customer object if found, None otherwise
        """
        for customer in self.customers:
            if customer.id == customer_id:
                return customer
        return None


# Create a global instance for easy access
customer_store = CustomerStore()
