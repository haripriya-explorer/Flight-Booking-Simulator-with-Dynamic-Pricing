

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
import base64
import uvicorn

from models import (
    FlightSearch, 
    FlightResponse, 
    FlightDetail, 
    BookingRequest, 
    BookingResponse,
    PricingResponse
)
from db_config import get_db_connection
from pricing_engine import calculate_dynamic_price
from utils import generate_pnr, calculate_refund_percentage, format_price, format_datetime

app = FastAPI(
    title="Flight Booking API",
    description="API for flight search, pricing, and booking",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Search flights endpoint
@app.get("/api/flights/search", response_model=List[FlightResponse])
async def search_flights(
    origin: str = Query(..., min_length=3, max_length=3, description="Origin airport code"),
    destination: str = Query(..., min_length=3, max_length=3, description="Destination airport code"),
    departure_date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    seat_class: str = Query("Economy", description="Seat class (Economy, Business, First)"),
    sort_by: Optional[str] = Query(None, description="Sort by price, duration, departure_time")
):
    """
    Search for flights based on origin, destination, and date
    """
    try:
        # Validate date format
        datetime.strptime(departure_date, "%Y-%m-%d")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query flights
        cursor.execute("""
            SELECT f.flight_id, f.flight_number, a.airline_name, 
                   f.origin, f.destination, f.departure_time, f.arrival_time,
                   f.base_price, f.total_seats
            FROM Flights f
            JOIN Airlines a ON f.airline_id = a.airline_id
            WHERE f.origin = ? AND f.destination = ? 
            AND DATE(f.departure_time) = ?
        """, (origin, destination, departure_date))
        
        flights = []
        for row in cursor.fetchall():
            flight_id, flight_number, airline_name, origin, destination, departure_time, arrival_time, base_price, total_seats = row
            
            # Get seat availability
            cursor.execute("""
                SELECT available_seats, price_multiplier 
                FROM Seats 
                WHERE flight_id = ? AND seat_class = ?
            """, (flight_id, seat_class))
            
            seat_info = cursor.fetchone()
            if not seat_info:
                continue  # Skip if seat class not available
                
            available_seats, price_multiplier = seat_info
            
            # Calculate dynamic price
            dynamic_price = calculate_dynamic_price(
                base_price=base_price,
                seat_class_multiplier=price_multiplier,
                available_seats=available_seats,
                total_seats=total_seats,
                departure_time=departure_time
            )
            
            flights.append({
                "flight_id": flight_id,
                "flight_number": flight_number,
                "airline_name": airline_name,
                "origin": origin,
                "destination": destination,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "base_price": base_price,
                "dynamic_price": dynamic_price,
                "available_seats": available_seats,
                "seat_class": seat_class
            })
        
        # Sort flights if requested
        if sort_by:
            if sort_by == "price":
                flights.sort(key=lambda x: x["dynamic_price"])
            elif sort_by == "duration":
                flights.sort(key=lambda x: (
                    datetime.strptime(x["arrival_time"], "%Y-%m-%d %H:%M:%S") - 
                    datetime.strptime(x["departure_time"], "%Y-%m-%d %H:%M:%S")
                ).total_seconds())
            elif sort_by == "departure_time":
                flights.sort(key=lambda x: x["departure_time"])
        
        conn.close()
        return flights
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get flight details endpoint
@app.get("/api/flights/{flight_id}", response_model=FlightDetail)
async def get_flight_details(
    flight_id: int,
    seat_class: str = Query("Economy", description="Seat class (Economy, Business, First)")
):
    """
    Get detailed information about a specific flight
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get flight details
        cursor.execute("""
            SELECT f.flight_id, f.flight_number, a.airline_name, 
                   f.origin, f.destination, f.departure_time, f.arrival_time,
                   f.base_price, f.total_seats
            FROM Flights f
            JOIN Airlines a ON f.airline_id = a.airline_id
            WHERE f.flight_id = ?
        """, (flight_id,))
        
        flight = cursor.fetchone()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
            
        flight_id, flight_number, airline_name, origin, destination, departure_time, arrival_time, base_price, total_seats = flight
        
        # Get seat availability
        cursor.execute("""
            SELECT seat_id, seat_class, initial_inventory, available_seats, price_multiplier 
            FROM Seats 
            WHERE flight_id = ?
        """, (flight_id,))
        
        seats = []
        for row in cursor.fetchall():
            seat_id, seat_class_db, initial_inventory, available_seats, price_multiplier = row
            seats.append({
                "seat_id": seat_id,
                "seat_class": seat_class_db,
                "initial_inventory": initial_inventory,
                "available_seats": available_seats,
                "price_multiplier": price_multiplier
            })
        
        # Get specific seat class info
        seat_info = next((s for s in seats if s["seat_class"] == seat_class), None)
        if not seat_info:
            raise HTTPException(status_code=404, detail=f"Seat class {seat_class} not available")
        
        # Calculate dynamic price
        dynamic_price = calculate_dynamic_price(
            base_price=base_price,
            seat_class_multiplier=seat_info["price_multiplier"],
            available_seats=seat_info["available_seats"],
            total_seats=total_seats,
            departure_time=departure_time
        )
        
        conn.close()
        
        return {
            "flight_id": flight_id,
            "flight_number": flight_number,
            "airline_name": airline_name,
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "base_price": base_price,
            "dynamic_price": dynamic_price,
            "seat_class": seat_class,
            "available_seats": seat_info["available_seats"],
            "seats_available": seats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Create booking endpoint
@app.post("/api/bookings", response_model=BookingResponse)
async def create_booking(booking: BookingRequest):
    booking_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = None
    try:
        conn = get_db_connection()
        conn.isolation_level = None
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            "SELECT flight_id, base_price, total_seats, departure_time FROM Flights WHERE flight_id = ?",
            (booking.flight_id,)
        )
        flight = cursor.fetchone()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        flight_id, base_price, total_seats, departure_time = flight
        cursor.execute(
            """
            SELECT available_seats, price_multiplier
            FROM Seats
            WHERE flight_id = ? AND seat_class = ?
            """,
            (booking.flight_id, booking.seat_class)
        )
        seat_info = cursor.fetchone()
        if not seat_info:
            raise HTTPException(status_code=404, detail=f"Seat class {booking.seat_class} not available")
        available_seats, price_multiplier = seat_info
        if available_seats < booking.seats_count:
            raise HTTPException(
                status_code=409,
                detail=f"Only {available_seats} seats available, requested {booking.seats_count}"
            )
        price_per_seat = calculate_dynamic_price(
            base_price=base_price,
            seat_class_multiplier=price_multiplier,
            available_seats=available_seats,
            total_seats=total_seats,
            departure_time=departure_time
        )
        total_price = round(price_per_seat * booking.seats_count, 2)
        pnr = generate_pnr()
        cursor.execute(
            """
            INSERT INTO Bookings (flight_id, user_id, seat_class, seats_booked, final_price, booking_date, status, pnr)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking.flight_id,
                booking.user_id,
                booking.seat_class,
                booking.seats_count,
                total_price,
                booking_timestamp,
                "Confirmed",
                pnr
            )
        )
        booking_id = cursor.lastrowid
        passengers = []
        for passenger in booking.passengers or []:
            passenger_dict = passenger.dict()
            passengers.append(passenger_dict)
            cursor.execute(
                """
                INSERT INTO Passengers (booking_id, first_name, last_name, email, phone)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    booking_id,
                    passenger_dict.get("first_name"),
                    passenger_dict.get("last_name"),
                    passenger_dict.get("email"),
                    passenger_dict.get("phone")
                )
            )
        cursor.execute(
            """
            UPDATE Seats
            SET available_seats = available_seats - ?
            WHERE flight_id = ? AND seat_class = ?
            """,
            (booking.seats_count, booking.flight_id, booking.seat_class)
        )
        cursor.execute(
            """
            INSERT INTO Transactions (booking_id, amount, payment_method, status, transaction_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (booking_id, total_price, booking.payment_method, "Completed", booking_timestamp)
        )
        cursor.execute(
            """
            INSERT INTO BookingHistory (booking_id, action, details, performed_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                booking_id,
                "CREATED",
                f"Booked {booking.seats_count} seats in {booking.seat_class}",
                booking_timestamp
            )
        )
        conn.commit()
        return {
            "success": True,
            "message": "Booking created successfully",
            "booking": {
                "booking_id": booking_id,
                "flight_id": booking.flight_id,
                "user_id": booking.user_id,
                "seat_class": booking.seat_class,
                "seats_booked": booking.seats_count,
                "final_price": total_price,
                "booking_date": booking_timestamp,
                "status": "Confirmed",
                "pnr": pnr,
                "passengers": passengers
            },
            "pricing_summary": {
                "price_per_seat": price_per_seat,
                "seats_booked": booking.seats_count,
                "total_price": total_price
            }
        }
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.post("/api/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: int):
    cancellation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = None
    try:
        conn = get_db_connection()
        conn.isolation_level = None
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            """
            SELECT booking_id, flight_id, seat_class, seats_booked, final_price, status
            FROM Bookings
            WHERE booking_id = ?
            """,
            (booking_id,)
        )
        booking = cursor.fetchone()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking[5] == "Cancelled":
            return {
                "success": True,
                "booking_id": booking_id,
                "status": "Cancelled",
                "refund": {
                    "percentage": 0,
                    "amount": 0.0
                }
            }
        cursor.execute(
            "SELECT departure_time FROM Flights WHERE flight_id = ?",
            (booking[1],)
        )
        flight = cursor.fetchone()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found for booking")
        refund_percentage = calculate_refund_percentage(flight[0])
        refund_amount = round((booking[4] * refund_percentage) / 100, 2)
        cursor.execute(
            """
            SELECT initial_inventory, available_seats
            FROM Seats
            WHERE flight_id = ? AND seat_class = ?
            """,
            (booking[1], booking[2])
        )
        seat_row = cursor.fetchone()
        if not seat_row:
            raise HTTPException(status_code=404, detail="Seat configuration not found")
        new_available = seat_row[1] + booking[3]
        if new_available > seat_row[0]:
            new_available = seat_row[0]
        cursor.execute(
            "UPDATE Bookings SET status = ? WHERE booking_id = ?",
            ("Cancelled", booking_id)
        )
        cursor.execute(
            "UPDATE Seats SET available_seats = ? WHERE flight_id = ? AND seat_class = ?",
            (new_available, booking[1], booking[2])
        )
        if refund_amount > 0:
            cursor.execute(
                """
                INSERT INTO Transactions (booking_id, amount, payment_method, status, transaction_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (booking_id, -refund_amount, "REFUND", "Completed", cancellation_time)
            )
        cursor.execute(
            """
            INSERT INTO BookingHistory (booking_id, action, details, performed_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                booking_id,
                "CANCELLED",
                f"Refund {refund_percentage}% amount {refund_amount}",
                cancellation_time
            )
        )
        conn.commit()
        return {
            "success": True,
            "booking_id": booking_id,
            "status": "Cancelled",
            "refund": {
                "percentage": refund_percentage,
                "amount": refund_amount
            }
        }
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if conn:
            conn.close()

# Get user bookings endpoint
@app.get("/api/users/{user_id}/bookings")
async def get_user_bookings(user_id: int):
    """
    Get all bookings for a specific user
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.booking_id, b.flight_id, b.seat_class, b.seats_booked, 
                   b.final_price, b.booking_date, b.status, b.pnr,
                   f.flight_number, f.origin, f.destination, 
                   f.departure_time, f.arrival_time, a.airline_name
            FROM Bookings b
            JOIN Flights f ON b.flight_id = f.flight_id
            JOIN Airlines a ON f.airline_id = a.airline_id
            WHERE b.user_id = ?
            ORDER BY b.booking_date DESC
        """, (user_id,))
        
        bookings = []
        for row in cursor.fetchall():
            (booking_id, flight_id, seat_class, seats_booked, 
             final_price, booking_date, status, pnr,
             flight_number, origin, destination, 
             departure_time, arrival_time, airline_name) = row
             
            bookings.append({
                "booking_id": booking_id,
                "flight_id": flight_id,
                "flight_number": flight_number,
                "airline_name": airline_name,
                "origin": origin,
                "destination": destination,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "seat_class": seat_class,
                "seats_booked": seats_booked,
                "final_price": final_price,
                "booking_date": booking_date,
                "status": status,
                "pnr": pnr
            })
        
        conn.close()
        
        return {
            "success": True,
            "user_id": user_id,
            "count": len(bookings),
            "bookings": bookings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get pricing endpoint
@app.get("/api/pricing/flight/{flight_id}", response_model=PricingResponse)
async def get_flight_pricing(
    flight_id: int,
    seat_class: str = Query("Economy", description="Seat class (Economy, Business, First)"),
    seats: int = Query(1, ge=1, le=9, description="Number of seats")
):
    """
    Get pricing breakdown for a flight
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get flight details
        cursor.execute("""
            SELECT flight_number, base_price, total_seats, departure_time
            FROM Flights WHERE flight_id = ?
        """, (flight_id,))
        
        flight = cursor.fetchone()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
            
        flight_number, base_price, total_seats, departure_time = flight
        
        # Get seat availability
        cursor.execute("""
            SELECT available_seats, price_multiplier 
            FROM Seats 
            WHERE flight_id = ? AND seat_class = ?
        """, (flight_id, seat_class))
        
        seat_info = cursor.fetchone()
        if not seat_info:
            raise HTTPException(status_code=404, detail=f"Seat class {seat_class} not available")
            
        available_seats, price_multiplier = seat_info
        
        # Calculate dynamic price
        dynamic_price = calculate_dynamic_price(
            base_price=base_price,
            seat_class_multiplier=price_multiplier,
            available_seats=available_seats,
            total_seats=total_seats,
            departure_time=departure_time
        )
        
        # Calculate pricing factors
        base_price_for_class = base_price * price_multiplier
        price_difference = dynamic_price - base_price_for_class
        total_price = dynamic_price * seats
        
        # Calculate occupancy ratio
        occupancy_ratio = (total_seats - available_seats) / total_seats
        
        # Calculate days until departure
        departure_date = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
        days_until_departure = (departure_date - datetime.now()).days + 1
        if days_until_departure < 0:
            days_until_departure = 0
        
        conn.close()
        
        return {
            "success": True,
            "flight_number": flight_number,
            "flight_id": flight_id,
            "seat_class": seat_class,
            "base_price": base_price,
            "seat_class_multiplier": price_multiplier,
            "base_price_for_class": base_price_for_class,
            "dynamic_price": dynamic_price,
            "price_difference": price_difference,
            "seats_requested": seats,
            "total_price": total_price,
            "pricing_factors": {
                "occupancy_ratio": occupancy_ratio,
                "available_seats": available_seats,
                "total_seats": total_seats,
                "days_until_departure": days_until_departure
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=5000, reload=True)