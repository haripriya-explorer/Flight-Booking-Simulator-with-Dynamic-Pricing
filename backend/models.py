"""
Flight Booking System - Data Models
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date

class FlightSearch(BaseModel):
    """Flight search request parameters"""
    origin: str = Field(..., min_length=3, max_length=3, description="Origin airport code")
    destination: str = Field(..., min_length=3, max_length=3, description="Destination airport code")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    seat_class: str = Field("Economy", description="Seat class (Economy, Business, First)")
    sort_by: Optional[str] = Field(None, description="Sort by price, duration, departure_time")
    
    @validator('departure_date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    @validator('seat_class')
    def validate_seat_class(cls, v):
        valid_classes = ["Economy", "Business", "First"]
        if v not in valid_classes:
            raise ValueError(f"Seat class must be one of {valid_classes}")
        return v
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        if v is None:
            return v
        valid_sort = ["price", "duration", "departure_time", "arrival_time"]
        if v not in valid_sort:
            raise ValueError(f"Sort by must be one of {valid_sort}")
        return v

class SeatInfo(BaseModel):
    """Seat information"""
    seat_id: int
    seat_class: str
    initial_inventory: int
    available_seats: int
    price_multiplier: float

class PassengerInfo(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None

class FlightResponse(BaseModel):
    """Flight search response model"""
    flight_id: int
    flight_number: str
    airline_name: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    base_price: float
    dynamic_price: float
    available_seats: int
    seat_class: str

class FlightDetail(BaseModel):
    """Detailed flight information"""
    flight_id: int
    flight_number: str
    airline_name: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    base_price: float
    dynamic_price: float
    seat_class: str
    available_seats: int
    seats_available: List[SeatInfo]

class BookingRequest(BaseModel):
    """Booking creation request"""
    flight_id: int = Field(..., description="Flight ID")
    user_id: int = Field(..., description="User ID")
    seat_class: str = Field("Economy", description="Seat class (Economy, Business, First)")
    seats_count: int = Field(1, ge=1, le=9, description="Number of seats to book")
    payment_method: str = Field("Credit Card", description="Payment method")
    passengers: Optional[List[PassengerInfo]] = None
    
    @validator('seat_class')
    def validate_seat_class(cls, v):
        valid_classes = ["Economy", "Business", "First"]
        if v not in valid_classes:
            raise ValueError(f"Seat class must be one of {valid_classes}")
        return v
    
    @validator('passengers', always=True)
    def validate_passengers(cls, v, values):
        if v is None:
            return []
        seats = values.get('seats_count')
        if seats and len(v) != seats:
            raise ValueError("Number of passengers must match seats_count")
        return v

class BookingDetail(BaseModel):
    """Booking details"""
    booking_id: int
    flight_id: int
    user_id: int
    seat_class: str
    seats_booked: int
    final_price: float
    booking_date: str
    status: str
    pnr: str
    passengers: Optional[List[PassengerInfo]] = None

class PricingSummary(BaseModel):
    """Pricing summary"""
    price_per_seat: float
    seats_booked: int
    total_price: float

class BookingResponse(BaseModel):
    """Booking creation response"""
    success: bool
    message: str
    booking: BookingDetail
    pricing_summary: PricingSummary

class PricingFactors(BaseModel):
    """Pricing factors"""
    occupancy_ratio: float
    available_seats: int
    total_seats: int
    days_until_departure: float
    demand_level: Optional[str] = "medium"
    occupancy_multiplier: Optional[float] = None
    time_multiplier: Optional[float] = None
    demand_multiplier: Optional[float] = None

class PricingResponse(BaseModel):
    """Flight pricing response"""
    success: bool
    flight_number: str
    flight_id: int
    seat_class: str
    base_price: float
    seat_class_multiplier: float
    base_price_for_class: float
    dynamic_price: float
    price_difference: float
    seats_requested: int
    total_price: float
    pricing_factors: PricingFactors