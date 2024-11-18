# myapp/utils.py
from io import BytesIO
import base64
import qrcode
import json
from . models import QRCode, UserEntry
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

def generate_qr_code(data):
    """Generate a QR code image encoded in base64."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(json.dumps(data))  # Convert dict to JSON string
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return qr_code_base64

def export_qr_code(request, user_entry_id):
    try:
        # Fetch the UserEntry object using the provided user_entry_id
        user_entry = get_object_or_404(UserEntry, entry_id=user_entry_id)

        # Get the QR code for the user entry
        qr_code = QRCode.objects.get(entry_id=user_entry)

        # Create an in-memory image buffer for the QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(user_entry.entry_id)  # Data can be entry_id or any other unique identifier
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Set the filename to the combination of fname and lname
        file_name = f"{user_entry.fname}_{user_entry.lname}_qr_code.png"

        # Set the content type and provide the image as a downloadable response
        response = HttpResponse(buffer, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        return response

    except QRCode.DoesNotExist:
        # Handle case where QR code doesn't exist for the user entry
        return HttpResponse("QR Code not found.", status=404)
    except Exception as e:
        # Handle unexpected errors
        return HttpResponse(f"An error occurred: {str(e)}", status=500)