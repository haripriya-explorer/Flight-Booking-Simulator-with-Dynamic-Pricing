"""
Flight Booking System - Dynamic Pricing Engine
Calculates dynamic prices based on various factors
"""

from datetime import datetime, timedelta


def calculate_dynamic_price(
    base_price: float,
    seat_class_multiplier: float,
    available_seats: int,
    total_seats: int,
    departure_time: str,
    demand_level: str = "medium"
) -> float:
    price = base_price * seat_class_multiplier
    occupancy_ratio = (total_seats - available_seats) / total_seats
    occupancy_multiplier = calculate_occupancy_multiplier(occupancy_ratio)
    time_multiplier = calculate_time_multiplier(departure_time)
    demand_multiplier = calculate_demand_multiplier(demand_level)
    final_price = price * occupancy_multiplier * time_multiplier * demand_multiplier
    return round(final_price, 2)


def calculate_occupancy_multiplier(occupancy_ratio: float) -> float:
    if occupancy_ratio >= 0.8:
        return 1.5
    if occupancy_ratio >= 0.6:
        return 1.35
    if occupancy_ratio >= 0.4:
        return 1.15
    return 1.0


def calculate_time_multiplier(departure_time: str) -> float:
    departure_date = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    days_until_departure = (departure_date - now).total_seconds() / (24 * 3600)
    if days_until_departure <= 1:
        return 2.0
    if days_until_departure <= 3:
        return 1.8
    if days_until_departure <= 7:
        return 1.5
    if days_until_departure <= 14:
        return 1.25
    if days_until_departure <= 30:
        return 1.1
    return 1.0


def calculate_demand_multiplier(demand_level: str) -> float:
    level = demand_level.lower()
    if level == "high":
        return 1.4
    if level == "low":
        return 0.8
    return 1.0


def get_pricing_factors(
    available_seats: int,
    total_seats: int,
    departure_time: str,
    demand_level: str = "medium",
    recent_bookings: int = 0
) -> dict:
    occupancy_ratio = (total_seats - available_seats) / total_seats
    departure_date = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
    days_until_departure = (departure_date - datetime.now()).days + 1
    if days_until_departure < 0:
        days_until_departure = 0
    booking_velocity = calculate_booking_velocity(recent_bookings, total_seats)
    return {
        "occupancy_ratio": round(occupancy_ratio, 3),
        "available_seats": available_seats,
        "total_seats": total_seats,
        "days_until_departure": days_until_departure,
        "demand_level": demand_level,
        "recent_bookings": recent_bookings,
        "booking_velocity": booking_velocity,
        "occupancy_multiplier": calculate_occupancy_multiplier(occupancy_ratio),
        "time_multiplier": calculate_time_multiplier(departure_time),
        "demand_multiplier": calculate_demand_multiplier(demand_level)
    }


def determine_demand_level(occupancy_ratio: float, booking_velocity: float, days_until_departure: float) -> str:
    if occupancy_ratio >= 0.75 or booking_velocity >= 0.25 or days_until_departure <= 3:
        return "high"
    if occupancy_ratio <= 0.3 and booking_velocity <= 0.08 and days_until_departure > 14:
        return "low"
    return "medium"


def calculate_booking_velocity(recent_bookings: int, total_seats: int) -> float:
    if total_seats <= 0:
        return 0.0
    velocity = recent_bookings / total_seats
    return round(velocity, 4)
