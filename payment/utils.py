import razorpay
from django.conf import settings
def get_razorpay_client():
    return razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))