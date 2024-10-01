from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import ChoiceList, Clashes, Faculty, MyUser, Student
from ..allocation_function import allocate
from django.contrib import messages
from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from django.core.mail import EmailMessage


@authorize_resource
def generate_pdf(request, id):
    # Fetch all students from the database
    allocations = ChoiceList.objects.all()

    for allocation in allocations:
        if allocation.event.id != id:
            continue

        # Create a PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        # Get the default stylesheet and customize heading
        styles = getSampleStyleSheet()
        heading_style = styles['Heading1']  # Use 'Heading1' style for large font
        heading_style.alignment = 1  # Center alignment
        heading_style.fontSize = 24  # Large font size
        heading_style.textColor = colors.HexColor("#2E8B57")  # Dark green heading color

        # Create the heading paragraph
        heading = Paragraph("PROJECT ALLOCATION DETAILS", heading_style)

        # Prepare the student details in two columns: field name and field value
        data = [
            ['Field', 'Details'],  # Table header
            ['Name', allocation.student.user.username],  # Student's name
            ['Professor', allocation.current_allocation.user.username],  # Professor name
            ['Email', allocation.student.user.email],  # Email address
            ['Date of Allocation', datetime.now().strftime("%Y-%m-%d")]  # Allocation date
        ]

        # Create the table with two columns (Field and Details)
        table = Table(data, colWidths=[2*inch, 4*inch])

        # Define table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)

        # Build the PDF with the heading and the table
        elements = []
        elements.append(heading)
        elements.append(Spacer(1, 0.5*inch))  # Add some space between heading and table
        elements.append(table)
        doc.build(elements)

        # Get the PDF content from the buffer
        pdf = buffer.getvalue()
        buffer.close()

        # Create the email for the specific student
        email = EmailMessage(
            subject='Your Project Allotment Details',
            body=f"Dear {data[1][1]},\n\nPlease find attached your project allotment details.",
            from_email='btechalloc@gmail.com',
            to=[data[3][1]],  # Send to the student's email
        )

        # Attach the personalized PDF
        email.attach('project_allotment.pdf', pdf, 'application/pdf')

        # Send the email
        email.send()

    # Return a response to confirm that emails have been sent


    messages.success(request, "Allocation reports have been sent successfully to all students."),
    return HttpResponseRedirect(reverse('create_cluster', args=(id,)))

