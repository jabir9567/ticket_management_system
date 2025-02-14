from decimal import Decimal
import requests
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Booking, Reservation
from events.models import Event, PromoCode
from .serializers import BookingSerializer, ReservationSerializer


class ReserveTicketView(APIView):
    def post(self, request):
        data = request.data
        event = get_object_or_404(Event, event_id=data['event_id'])
        
        # Calculate total number of tickets requested
        total_tickets = sum(t['quantity'] for t in data['tickets'])
        if len(data['seat_selection']) != total_tickets:
            return Response(
                {"error": "The number of seat selections must match the total number of tickets."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check availability of seats
        unavailable_seats = []
        for seat in data['seat_selection']:
            if event.seats.get(seat) == "booked":
                unavailable_seats.append(seat)
            else:
                # Look through active reservations for the event
                active_reservations = Reservation.objects.filter(event=event)
                for reservation in active_reservations:
                    if not reservation.is_expired() and seat in reservation.seat_selection:
                        unavailable_seats.append(seat)
                        break
        if unavailable_seats:
            return Response({"error": "One or more selected seats are no longer available."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate base price from tickets
        base_price = sum(
            t['quantity'] * (event.vip_price if t['type'] == 'VIP' else event.standard_price)
            for t in data['tickets']
        )
        base_price = Decimal(base_price)

        # Apply dynamic pricing multiplier (if provided)
        dynamic_pricing_multiplier = Decimal(data.get('dynamic_pricing_multiplier', 1))
        base_price *= dynamic_pricing_multiplier
        


        # Group discount validation and application
        if total_tickets >= 4:
            # Apply the group discount
            base_price *= Decimal('0.90')  # Apply 10% discount


    # Promo code validation and discount application
        promo_code = data.get('promo_code')
        if promo_code:
            try:
                # Retrieve only active promo codes.
                promo = PromoCode.objects.filter(code=promo_code, active=True).first()
                if not promo:
                    return Response(
                        {'error': 'Promo code is not valid or has reached its usage limit.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Apply the discount based on the type of discount
                discount_type = promo.discount_type
                discount_value = promo.discount_value
                if discount_type == 'percentage':
                    base_price *= (Decimal('100') - discount_value) / Decimal('100')
                elif discount_type == 'fixed':
                    base_price = base_price - discount_value if base_price > discount_value else Decimal('0')

            except Exception as e:
                return Response(
                    {'error': f'Error applying promo code: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

                

        # Service Fees: 5% of base_price plus $2 per ticket
        service_fees = (base_price * Decimal('0.05')) + (Decimal('2') * total_tickets)

        # Cancellation Insurance: adds $20 if opted in
        insurance = Decimal('20') if data.get('cancellation_insurance') else Decimal('0')

        total_cost = base_price + service_fees + insurance
        total_cost = total_cost.quantize(Decimal('0.01'))

        # Mark the seats as "reserved" in the event's seats dictionary
        for seat in data['seat_selection']:
            event.seats[seat] = "reserved"
        event.save()

        # Create a temporary Reservation record
        reservation = Reservation.objects.create(
            event=event,
            user_id=data['user_id'],
            tickets=data['tickets'],
            seat_selection=data['seat_selection'],
            promo_code=promo_code,
            total_cost=total_cost,
            cancellation_insurance=data.get('cancellation_insurance', False)
        )

        serializer = ReservationSerializer(reservation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class ConfirmPaymentView(APIView):
    def post(self, request):
        reservation_id = request.data.get('reservation_id')
        user_id = request.data.get('user_id')
        payment_status = request.data.get('payment_status')

        if not reservation_id or not user_id or not payment_status:
            return Response({"error": "Reservation ID, user ID, and payment status are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        reservation = get_object_or_404(Reservation, id=reservation_id)

        # Check if the reservation has expired
        if reservation.is_expired():
            # Release reserved seats back to available
            event = reservation.event
            for seat in reservation.seat_selection:
                if event.seats.get(seat) == "reserved":
                    event.seats[seat] = "available"
            event.save()
            reservation.delete()
            return Response({"error": "Reservation expired. Please try booking again."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Handle payment status
        if payment_status == "rejected":
            # Release reserved seats back to available
            event = reservation.event
            for seat in reservation.seat_selection:
                if event.seats.get(seat) == "reserved":
                    event.seats[seat] = "available"
            event.save()
            reservation.delete()
            return Response({"message": "Payment rejected. Seats have been released."},
                            status=status.HTTP_200_OK)

        elif payment_status == "success":
            # Update the seats to "booked"
            event = reservation.event
            for seat in reservation.seat_selection:
                event.seats[seat] = "booked"
            event.save()
            # Increment promo code usage count if a promo code is applied
            if reservation.promo_code:
                promo = PromoCode.objects.filter(code=reservation.promo_code, active=True).first()
                if promo:
                    promo.usage_count += 1
                    promo.save()
                    
            # Create a permanent Booking record from the reservation details
            booking = Booking.objects.create(
                event=reservation.event,
                user_id=reservation.user_id,
                tickets=reservation.tickets,
                seat_selection=reservation.seat_selection,
                promo_code=reservation.promo_code,
                total_cost=reservation.total_cost,
                cancellation_insurance=reservation.cancellation_insurance
            )
            reservation.delete()  # Remove the temporary reservation

            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response({"error": "Invalid payment status."},
                            status=status.HTTP_400_BAD_REQUEST)
    


class CheckSeatAvailabilityView(APIView):
    def get(self, request, event_id):
        event = get_object_or_404(Event, event_id=event_id)
        seat_map = event.seats  # Assuming 'seats' is a JSONField representing seat availability
        return Response(seat_map, status=status.HTTP_200_OK)
    

       
class CancelTicketView(APIView):
    def post(self, request):
        data = request.data
        booking_id = data.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Calculate the refund amount
        if booking.cancellation_insurance:
            refund_amount = booking.total_cost
            cancellation_fee = Decimal('0.00')
        else:
            cancellation_fee = booking.total_cost * Decimal('0.15')
            refund_amount = booking.total_cost - cancellation_fee
        
        # Release the seats
        event = booking.event
        for seat in booking.seat_selection:
            if event.seats.get(seat) == "booked":
                event.seats[seat] = "available"
        event.save()
        
        # Delete the booking
        booking.delete()
        
        return Response({
            "status": "cancelled",
            "refund_amount": float(refund_amount),  # Convert Decimal to float for JSON serialization
            "cancellation_fee": float(cancellation_fee)
        }, status=status.HTTP_200_OK)
        
        
class TicketListView(APIView):
    def get(self, request):
        # Retrieve all bookings (both booked and cancelled)
        bookings = Booking.objects.all()
        
        # Serialize the booking data
        serializer = BookingSerializer(bookings, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

