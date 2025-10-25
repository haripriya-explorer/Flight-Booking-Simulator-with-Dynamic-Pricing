import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import plotly.express as px

# API Configuration
API_BASE_URL = "http://localhost:5000/api"

# Page configuration
st.set_page_config(
    page_title="Flight Booking System",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper functions
def format_price(price):
    """Format price with currency symbol"""
    return f"${price:.2f}"

def format_datetime(dt_str):
    """Format datetime string for display"""
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%b %d, %Y %I:%M %p")

def calculate_duration(departure, arrival):
    """Calculate flight duration"""
    dept = datetime.strptime(departure, "%Y-%m-%d %H:%M:%S")
    arrv = datetime.strptime(arrival, "%Y-%m-%d %H:%M:%S")
    duration = arrv - dept
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def api_request(endpoint, method="GET", data=None):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            st.error(f"Unsupported method: {method}")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Sidebar for user selection and navigation
st.sidebar.title("✈️ Flight Booking System")

# User selection
user_id = st.sidebar.selectbox(
    "Select User ID",
    options=[1, 2, 3],
    format_func=lambda x: f"User {x}"
)

# Navigation
page = st.sidebar.radio(
    "Navigation",
    options=["Search Flights", "My Bookings", "Pricing Analytics"]
)

# Initialize session state for booking flow
if "booking_flow" not in st.session_state:
    st.session_state.booking_flow = {
        "step": 0,  # 0: search, 1: flight selected, 2: passenger info, 3: payment, 4: confirmation
        "selected_flight": None,
        "passenger_info": [],
        "booking_id": None
    }

# Reset booking flow
if st.sidebar.button("New Search"):
    st.session_state.booking_flow = {
        "step": 0,
        "selected_flight": None,
        "passenger_info": [],
        "booking_id": None
    }

# Search Flights Page
if page == "Search Flights" and st.session_state.booking_flow["step"] == 0:
    st.title("Search Flights")
    
    # Search form
    with st.form("search_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            origin = st.selectbox(
                "From",
                options=["JFK", "LAX", "ORD", "LHR", "CDG", "FRA", "DXB", "SIN", "HND", "SYD"],
                format_func=lambda x: f"{x}"
            )
        
        with col2:
            destination = st.selectbox(
                "To",
                options=["LAX", "JFK", "ORD", "LHR", "CDG", "FRA", "DXB", "SIN", "HND", "SYD"],
                format_func=lambda x: f"{x}"
            )
        
        with col3:
            min_date = datetime.now().date() + timedelta(days=1)
            max_date = min_date + timedelta(days=90)
            departure_date = st.date_input(
                "Departure Date",
                min_value=min_date,
                max_value=max_date,
                value=min_date
            )
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            seat_class = st.selectbox(
                "Seat Class",
                options=["Economy", "Business"]
            )
        
        with col5:
            passengers = st.number_input(
                "Passengers",
                min_value=1,
                max_value=9,
                value=1
            )
        
        with col6:
            sort_by = st.selectbox(
                "Sort By",
                options=[None, "price", "duration", "departure_time"],
                format_func=lambda x: "Default" if x is None else x.replace("_", " ").title()
            )
        
        search_submitted = st.form_submit_button("Search Flights")
    
    # Process search
    if search_submitted:
        if origin == destination:
            st.error("Origin and destination cannot be the same")
        else:
            with st.spinner("Searching flights..."):
                # Format date as string
                date_str = departure_date.strftime("%Y-%m-%d")
                
                # Build query parameters
                params = f"?origin={origin}&destination={destination}&departure_date={date_str}&seat_class={seat_class}"
                if sort_by:
                    params += f"&sort_by={sort_by}"
                
                # Make API request
                flights = api_request(f"/flights/search{params}")
                
                if flights is None:
                    st.error("Failed to fetch flights")
                else:
                    flight_data = []
                    fetch_success = False
                    
                    if isinstance(flights, list):
                        flight_data = flights
                        fetch_success = True
                    elif isinstance(flights, dict):
                        fetch_success = flights.get("success", False)
                        flight_data = flights.get("flights", [])
                    else:
                        st.error("Unexpected response format from API")
                    
                    if fetch_success:
                        if not flight_data:
                            st.info("No flights found for the selected criteria")
                        else:
                            st.success(f"Found {len(flight_data)} flights")
                            
                            # Display flights
                            for flight in flight_data:
                                col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
                                
                                with col1:
                                    st.subheader(f"{flight['airline_name']}")
                                    st.caption(f"Flight {flight['flight_number']}")
                                
                                with col2:
                                    st.write(f"**{flight['origin']} → {flight['destination']}**")
                                    st.write(f"{format_datetime(flight['departure_time'])} → {format_datetime(flight['arrival_time'])}")
                                    st.caption(f"Duration: {calculate_duration(flight['departure_time'], flight['arrival_time'])}")
                                
                                with col3:
                                    st.write(f"**Price: {format_price(flight['dynamic_price'])}**")
                                    st.write(f"Seat Class: {flight['seat_class']}")
                                    st.caption(f"Available Seats: {flight['available_seats']}")
                                
                                with col4:
                                    if st.button("Select", key=f"select_{flight['flight_id']}"):
                                        # Store selected flight in session state
                                        st.session_state.booking_flow["step"] = 1
                                        st.session_state.booking_flow["selected_flight"] = flight
                                        st.session_state.booking_flow["passenger_count"] = passengers
                                        st.experimental_rerun()
                                
                                st.divider()
                    else:
                        if isinstance(flights, dict) and flights.get("message"):
                            st.error(flights.get("message"))
                        else:
                            st.error("Failed to fetch flights")

# Flight Selected - Passenger Information
elif page == "Search Flights" and st.session_state.booking_flow["step"] == 1:
    flight = st.session_state.booking_flow["selected_flight"]
    passenger_count = st.session_state.booking_flow["passenger_count"]
    
    st.title("Complete Your Booking")
    
    # Flight summary
    st.subheader("Flight Details")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**{flight['airline_name']}**")
        st.write(f"Flight {flight['flight_number']}")
    
    with col2:
        st.write(f"**{flight['origin']} → {flight['destination']}**")
        st.write(f"{format_datetime(flight['departure_time'])}")
        st.write(f"Duration: {calculate_duration(flight['departure_time'], flight['arrival_time'])}")
    
    with col3:
        st.write(f"**Price: {format_price(flight['dynamic_price'])} per seat**")
        st.write(f"Seat Class: {flight['seat_class']}")
        st.write(f"Total: {format_price(flight['dynamic_price'] * passenger_count)} ({passenger_count} passengers)")
    
    st.divider()
    
    # Passenger information form
    st.subheader("Passenger Information")
    
    with st.form("passenger_form"):
        passengers = []
        
        for i in range(passenger_count):
            st.write(f"**Passenger {i+1}**")
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name", key=f"first_name_{i}")
            
            with col2:
                last_name = st.text_input("Last Name", key=f"last_name_{i}")
            
            col3, col4 = st.columns(2)
            
            with col3:
                email = st.text_input("Email", key=f"email_{i}")
            
            with col4:
                phone = st.text_input("Phone", key=f"phone_{i}")
            
            passengers.append({
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone
            })
            
            if i < passenger_count - 1:
                st.divider()
        
        proceed = st.form_submit_button("Proceed to Payment")
    
    if proceed:
        # Validate passenger information
        valid = True
        for i, passenger in enumerate(passengers):
            if not passenger["first_name"] or not passenger["last_name"]:
                st.error(f"Please enter name for Passenger {i+1}")
                valid = False
        
        if valid:
            # Store passenger information
            st.session_state.booking_flow["passenger_info"] = passengers
            st.session_state.booking_flow["step"] = 2
            st.experimental_rerun()
    
    if st.button("← Back to Search"):
        st.session_state.booking_flow["step"] = 0
        st.experimental_rerun()

# Payment
elif page == "Search Flights" and st.session_state.booking_flow["step"] == 2:
    flight = st.session_state.booking_flow["selected_flight"]
    passenger_count = st.session_state.booking_flow["passenger_count"]
    passengers = st.session_state.booking_flow["passenger_info"]
    
    st.title("Payment")
    
    # Flight and price summary
    st.subheader("Booking Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Flight:** {flight['airline_name']} {flight['flight_number']}")
        st.write(f"**Route:** {flight['origin']} → {flight['destination']}")
        st.write(f"**Date:** {format_datetime(flight['departure_time'])}")
        st.write(f"**Seat Class:** {flight['seat_class']}")
    
    with col2:
        st.write(f"**Price per seat:** {format_price(flight['dynamic_price'])}")
        st.write(f"**Passengers:** {passenger_count}")
        st.write(f"**Total Price:** {format_price(flight['dynamic_price'] * passenger_count)}")
    
    st.divider()
    
    # Payment form
    with st.form("payment_form"):
        payment_method = st.selectbox(
            "Payment Method",
            options=["Credit Card", "Debit Card", "PayPal"]
        )
        
        if payment_method in ["Credit Card", "Debit Card"]:
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Card Number", placeholder="1234 5678 9012 3456")
            
            with col2:
                st.text_input("Cardholder Name", placeholder="John Doe")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.text_input("Expiry Date", placeholder="MM/YY")
            
            with col4:
                st.text_input("CVV", placeholder="123", type="password")
            
            with col5:
                st.text_input("Zip Code", placeholder="10001")
        
        elif payment_method == "PayPal":
            st.text_input("PayPal Email", placeholder="email@example.com")
        
        complete_payment = st.form_submit_button("Complete Payment")
    
    if complete_payment:
        with st.spinner("Processing payment..."):
            # Create booking request
            booking_data = {
                "flight_id": flight["flight_id"],
                "user_id": user_id,
                "seat_class": flight["seat_class"],
                "seats_count": passenger_count
            }
            
            # Make API request to create booking
            booking_response = api_request("/bookings", method="POST", data=booking_data)
            
            if booking_response and booking_response.get("success", False):
                # Store booking ID
                st.session_state.booking_flow["booking_id"] = booking_response["booking"]["booking_id"]
                st.session_state.booking_flow["booking_details"] = booking_response["booking"]
                st.session_state.booking_flow["step"] = 3
                st.experimental_rerun()
            else:
                st.error("Failed to create booking. Please try again.")
    
    if st.button("← Back to Passenger Information"):
        st.session_state.booking_flow["step"] = 1
        st.experimental_rerun()

# Booking Confirmation
elif page == "Search Flights" and st.session_state.booking_flow["step"] == 3:
    booking = st.session_state.booking_flow["booking_details"]
    
    st.title("Booking Confirmed! ✓")
    
    # Display confirmation details
    st.success(f"Your booking has been confirmed with PNR: **{booking['pnr']}**")
    
    st.subheader("Booking Details")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Booking ID:** {booking['booking_id']}")
        st.write(f"**PNR:** {booking['pnr']}")
        st.write(f"**Status:** {booking['status']}")
        st.write(f"**Booking Date:** {booking['booking_date']}")
    
    with col2:
        st.write(f"**Seat Class:** {booking['seat_class']}")
        st.write(f"**Seats Booked:** {booking['seats_booked']}")
        st.write(f"**Total Price:** {format_price(booking['final_price'])}")
    
    st.divider()
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("View My Bookings"):
            # Switch to My Bookings page
            st.session_state.booking_flow["step"] = 0
            st.experimental_rerun()
    
    with col2:
        if st.button("Download Receipt"):
            st.info("Receipt download functionality would be implemented here")
    
    with col3:
        if st.button("New Search"):
            # Reset booking flow
            st.session_state.booking_flow = {
                "step": 0,
                "selected_flight": None,
                "passenger_info": [],
                "booking_id": None
            }
            st.experimental_rerun()

# My Bookings Page
elif page == "My Bookings":
    st.title("My Bookings")
    
    with st.spinner("Loading your bookings..."):
        # Get user bookings
        bookings_response = api_request(f"/users/{user_id}/bookings")
        
        if bookings_response and bookings_response.get("success", False):
            bookings = bookings_response.get("bookings", [])
            
            if not bookings:
                st.info("You don't have any bookings yet")
            else:
                st.success(f"Found {len(bookings)} bookings")
                
                # Display bookings
                for booking in bookings:
                    col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
                    
                    with col1:
                        st.subheader(f"{booking['airline_name']}")
                        st.caption(f"Flight {booking['flight_number']}")
                        st.caption(f"PNR: {booking['pnr']}")
                    
                    with col2:
                        st.write(f"**{booking['origin']} → {booking['destination']}**")
                        st.write(f"{format_datetime(booking['departure_time'])}")
                        st.caption(f"Booked on: {booking['booking_date']}")
                    
                    with col3:
                        st.write(f"**{booking['seat_class']}**")
                        st.write(f"{booking['seats_booked']} seats")
                        st.write(f"Total: {format_price(booking['final_price'])}")
                    
                    with col4:
                        st.write(f"**{booking['status']}**")
                        if booking['status'] == 'Confirmed':
                            if st.button("Cancel", key=f"cancel_{booking['booking_id']}"):
                                st.info("Cancellation functionality would be implemented here")
                    
                    st.divider()
        else:
            st.error("Failed to load bookings")

# Pricing Analytics Page
elif page == "Pricing Analytics":
    st.title("Pricing Analytics")
    
    # Flight selection for analytics
    col1, col2 = st.columns(2)
    
    with col1:
        origin = st.selectbox(
            "Origin",
            options=["JFK", "LAX", "ORD", "LHR", "CDG", "FRA", "DXB", "SIN", "HND", "SYD"],
            key="analytics_origin"
        )
    
    with col2:
        destination = st.selectbox(
            "Destination",
            options=["LAX", "JFK", "ORD", "LHR", "CDG", "FRA", "DXB", "SIN", "HND", "SYD"],
            key="analytics_destination"
        )
    
    if st.button("Show Pricing Analysis"):
        if origin == destination:
            st.error("Origin and destination cannot be the same")
        else:
            with st.spinner("Loading pricing data..."):
                # This would normally call a pricing history API
                # For demo purposes, we'll generate sample data
                
                # Sample data for price history
                dates = pd.date_range(start=datetime.now(), periods=30, freq='D')
                economy_prices = [300 + i * 5 + (i % 7) * 20 for i in range(30)]
                business_prices = [600 + i * 10 + (i % 7) * 40 for i in range(30)]
                
                # Create DataFrame
                df = pd.DataFrame({
                    'Date': dates,
                    'Economy': economy_prices,
                    'Business': business_prices
                })
                
                # Plot price trends
                st.subheader(f"Price Trends: {origin} → {destination}")
                
                fig = px.line(
                    df, 
                    x='Date', 
                    y=['Economy', 'Business'],
                    title=f"Price Trends for {origin} to {destination}",
                    labels={'value': 'Price ($)', 'variable': 'Seat Class'},
                    color_discrete_sequence=['#1f77b4', '#ff7f0e']
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Price statistics
                st.subheader("Price Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Average Economy Price", f"${df['Economy'].mean():.2f}")
                
                with col2:
                    st.metric("Average Business Price", f"${df['Business'].mean():.2f}")
                
                with col3:
                    st.metric("Business/Economy Ratio", f"{df['Business'].mean() / df['Economy'].mean():.2f}x")
                
                # Occupancy impact on pricing
                st.subheader("Occupancy Impact on Pricing")
                
                # Sample data for occupancy impact
                occupancy_levels = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
                price_multipliers = [1.0, 1.0, 1.0, 1.0, 1.15, 1.15, 1.35, 1.35, 1.5]
                
                # Create DataFrame
                df_occupancy = pd.DataFrame({
                    'Occupancy': [f"{int(o*100)}%" for o in occupancy_levels],
                    'Price Multiplier': price_multipliers
                })
                
                # Plot occupancy impact
                fig_occupancy = px.bar(
                    df_occupancy,
                    x='Occupancy',
                    y='Price Multiplier',
                    title="Price Multiplier by Occupancy Level",
                    labels={'Price Multiplier': 'Multiplier', 'Occupancy': 'Occupancy Level'},
                    color='Price Multiplier',
                    color_continuous_scale='Viridis'
                )
                
                st.plotly_chart(fig_occupancy, use_container_width=True)
                
                # Time to departure impact
                st.subheader("Time to Departure Impact")
                
                # Sample data for time impact
                days_to_departure = [1, 3, 7, 14, 30, 60, 90]
                time_multipliers = [2.0, 1.8, 1.5, 1.25, 1.1, 1.0, 1.0]
                
                # Create DataFrame
                df_time = pd.DataFrame({
                    'Days to Departure': days_to_departure,
                    'Price Multiplier': time_multipliers
                })
                
                # Plot time impact
                fig_time = px.line(
                    df_time,
                    x='Days to Departure',
                    y='Price Multiplier',
                    title="Price Multiplier by Days to Departure",
                    labels={'Price Multiplier': 'Multiplier', 'Days to Departure': 'Days Before Flight'},
                    markers=True
                )
                
                st.plotly_chart(fig_time, use_container_width=True)

# Footer
st.sidebar.divider()
st.sidebar.caption("Flight Booking System - Dynamic Pricing")
st.sidebar.caption("© 2023 All Rights Reserved")

if __name__ == "__main__":
    # This is used when running the file directly
    pass