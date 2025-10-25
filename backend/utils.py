"""
Flight Booking System - Utility Functions
Helper functions for the booking system
"""

import random
import string
from datetime import datetime, timedelta

def generate_pnr(length=6):
    """
    Generate a random PNR (Passenger Name Record) code
    
    Args:
        length: Length of the PNR code (default: 6)
        
    Returns:
        Random alphanumeric PNR code
    """
    # Use uppercase letters and digits for PNR
    characters = string.ascii_uppercase + string.digits
    
    # Exclude similar looking characters
    characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    
    # Generate random PNR
    pnr = ''.join(random.choice(characters) for _ in range(length))
    
    return pnr

def format_price(price):
    """
    Format price with 2 decimal places
    
    Args:
        price: Price to format
        
    Returns:
        Formatted price string
    """
    return f"${price:.2f}"

def calculate_duration(departure_time, arrival_time):
    """
    Calculate flight duration in hours and minutes
    
    Args:
        departure_time: Departure time string
        arrival_time: Arrival time string
        
    Returns:
        Duration string in format "Xh Ym"
    """
    try:
        departure = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
        arrival = datetime.strptime(arrival_time, "%Y-%m-%d %H:%M:%S")
        
        duration = arrival - departure
        total_minutes = duration.total_seconds() / 60
        
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        
        return f"{hours}h {minutes}m"
    except:
        return "Unknown"

def calculate_refund_percentage(departure_time):
    """
    Calculate refund percentage based on time to departure
    
    Refund Policy:
    - More than 72 hours: 100%
    - 24-72 hours: 75%
    - 2-24 hours: 50%
    - Less than 2 hours: 0%
    
    Args:
        departure_time: Departure time string
        
    Returns:
        Refund percentage (0-100)
    """
    try:
        departure = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        # Calculate hours until departure
        hours_until_departure = (departure - now).total_seconds() / 3600
        
        if hours_until_departure > 72:
            return 100
        elif hours_until_departure >= 24:
            return 75
        elif hours_until_departure >= 2:
            return 50
        else:
            return 0
    except:
        return 0

def format_datetime(date_string, include_time=True):
    """
    Format datetime string for display
    
    Args:
        date_string: Datetime string
        include_time: Whether to include time in output
        
    Returns:
        Formatted datetime string
    """
    try:
        dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        
        if include_time:
            return dt.strftime("%b %d, %Y %I:%M %p")
        else:
            return dt.strftime("%b %d, %Y")
    except:
        return date_string