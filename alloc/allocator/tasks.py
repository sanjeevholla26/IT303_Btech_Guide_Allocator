# tasks.py in your Django app
from celery import shared_task
from .email_sender import send_mail_page

@shared_task
def send_email_task(to_email, subject, message):
    try:
        send_mail_page(to_email, subject, message)
        return {'result': 'Email sent successfully'}
    except Exception as e:
        return {'error': str(e)}
    

# @shared_task
# def generate_pdf_task(data):
#     pdf = generate_pdf(data)  # A function that generates a PDF
#     # Save or send the generated PDF