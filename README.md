# Flight Booking Simulator with Dynamic Pricing

A modern flight booking system with dynamic pricing that adjusts based on demand, seat availability, and time to departure.

## Project Structure

- **backend/**: FastAPI backend with flight search, booking, and pricing APIs
- **frontend/**: Streamlit-based web interface
- **db/**: Database schema and initialization scripts

## Features

- Flight search with filtering by origin, destination, date, and seat class
- Dynamic pricing based on demand, seat availability, and time to departure
- Booking management with passenger information
- User account management
- Pricing analytics and visualization

## Requirements

- Python 3.8+
- FastAPI
- Streamlit
- SQLite3
- Plotly (for analytics)

## Installation

1. Clone the repository
2. Install the required packages:

```bash
pip install fastapi uvicorn streamlit pandas plotly requests
```

3. Initialize the database:

```bash
cd db
python create_db.py
```

## Running the Application

1. Start the backend server:

```bash
cd backend
uvicorn backend:app --reload --port 5000
```

2. Start the frontend application:

```bash
cd frontend
streamlit run app.py
```

3. Open your browser and navigate to:
   - Frontend: http://localhost:8501
   - API Documentation: http://localhost:5000/docs

## API Endpoints

- `GET /api/health`: Health check endpoint
- `GET /api/flights/search`: Search for flights
- `GET /api/flights/{flight_id}`: Get flight details
- `POST /api/bookings`: Create a new booking
- `GET /api/users/{user_id}/bookings`: Get user bookings
- `GET /api/pricing/history/{flight_id}`: Get pricing history for a flight
- `GET /api/pricing/analytics`: Get pricing analytics

## Dynamic Pricing Algorithm

The system uses a sophisticated pricing algorithm that considers:

- Base price for the route
- Seat class multiplier (Economy, Business, First)
- Current seat availability percentage
- Time remaining until departure
- Historical booking patterns
- Seasonal demand factors

Prices are updated in real-time as bookings are made, ensuring optimal revenue management.