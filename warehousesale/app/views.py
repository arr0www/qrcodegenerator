from django.shortcuts import render, redirect
from .forms import UserEntryForm
from .models import UserEntry, Relative, QRCode
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils.dateparse import parse_datetime
import logging, datetime
from django.contrib import messages
from datetime import datetime
from . utils import generate_qr_code


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def submit_entries(request):
    """Process all entries in tempAdd and save them to the database."""
    if 'tempAdd' not in request.session:
        messages.error(request, 'No entries to submit.')
        return redirect('create_entry')

    temp_add = request.session.pop('tempAdd', [])  # Pop the tempAdd list
    submitted_entries = []  # New list to store entries along with QR codes

    for entry_data in temp_add:
        # Ensure arrival_date is a datetime object (if it's a string in ISO format)
        if 'arrival_date' in entry_data and isinstance(entry_data['arrival_date'], str):
            entry_data['arrival_date'] = parse_datetime(entry_data['arrival_date'])

        # Ensure r_fname and r_lname exist in the entry data
        r_fname = entry_data.get('r_fname')
        r_lname = entry_data.get('r_lname')

        if not r_fname or not r_lname:
            # Log and skip entries with missing required fields
            print(f"Error: Missing required fields (r_fname or r_lname) for entry: {entry_data}")
            messages.error(request, f"Missing required relative name fields for entry: {entry_data}")
            continue

        # Create or get the Relative object only if r_fname and r_lname are provided
        relative, created = Relative.objects.get_or_create(
            r_fname=r_fname,
            r_lname=r_lname,
            defaults={'r_department': entry_data.get('r_department', '')}
        )

        # Create the UserEntry object
        user_entry = UserEntry.objects.create(
            fname=entry_data['fname'],
            lname=entry_data['lname'],
            arrival_date=entry_data['arrival_date'],
            relative=relative,  # Associate the UserEntry with the Relative
            relationship=entry_data.get('relationship', ''),  # Default empty if not provided
            voucher_id=entry_data.get('voucher_id', '')  # Default empty if not provided
        )

        # Prepare data for the QR code generation
        qr_data = {
            "entry_id": user_entry.entry_id,
            "fname": user_entry.fname,
            "lname": user_entry.lname,
            "r_fname": user_entry.relative.r_fname,
            "r_lname": user_entry.relative.r_lname,
            "r_department": user_entry.relative.r_department,
            "voucher_id": user_entry.voucher_id,
            "arrival_date": user_entry.arrival_date.isoformat()  # Use ISO format for QR code data
        }

        # Generate QR code and create entry in the database
        qr_code = generate_qr_code(qr_data)
        QRCode.objects.create(entry_id=user_entry, qr_code=qr_code)

        # Prepare the entry data for submission, ensuring arrival_date is in ISO format
        submitted_entries.append({
            "entry_id": user_entry.entry_id,
            "fname": user_entry.fname,
            "lname": user_entry.lname,
            "arrival_date": user_entry.arrival_date.isoformat(),  # Store arrival_date in ISO format
            "qr_code": qr_code  # Store the QR code generated for each entry
        })

    # Store the submitted entries in the session for later display
    request.session['submitted_entries'] = submitted_entries

    return redirect('entry_success')


def entry_success(request):
    submitted_entries = request.session.get('submitted_entries', [])
    
    vouchers = UserEntry.objects.all()

    for entry in submitted_entries:
        if 'arrival_date' in entry:
            # Convert ISO string to datetime
            try:
                if isinstance(entry['arrival_date'], str):  # Check if it's an ISO string
                    entry['arrival_date'] = datetime.fromisoformat(entry['arrival_date'])
                elif isinstance(entry['arrival_date'], datetime):
                    # If it's already a datetime object, leave it as is
                    pass
            except (ValueError, TypeError):
                entry['arrival_date'] = None  # Handle invalid date format

    return render(request, 'entry_success.html', {'submitted_entries': submitted_entries, "vouchers":vouchers})


def addEntry(request):
    if request.method == 'POST':
        form = UserEntryForm(request.POST)
        if form.is_valid():
            entry_data = form.cleaned_data
            # Ensure arrival_date is in ISO format before saving to session
            if 'arrival_date' in entry_data:
                entry_data['arrival_date'] = entry_data['arrival_date'].isoformat()

            # Create the entry data from the form
            fname = entry_data.get('fname')
            lname = entry_data.get('lname')
            # Ensure that r_fname and r_lname are included if they exist
            r_fname = entry_data.get('r_fname')
            r_lname = entry_data.get('r_lname')

            # Check if this combination of fname and lname already exists in the database
            if UserEntry.objects.filter(fname=fname, lname=lname).exists():
                messages.error(request, 'This entry already exists in the database.')
                return redirect('create_entry')

            # Initialize tempAdd in the session if it doesn't exist
            if 'tempAdd' not in request.session:
                request.session['tempAdd'] = []

            # Check for duplicate entries in the session
            temp_add = request.session['tempAdd']
            for entry in temp_add:
                if entry.get('fname') == fname and entry.get('lname') == lname:
                    messages.error(request, 'This entry already exists in the session.')
                    return redirect('create_entry')

            # Append the new entry data to the list in the session
            entry_data['r_fname'] = r_fname
            entry_data['r_lname'] = r_lname
            request.session['tempAdd'].append(entry_data)
            request.session.modified = True  # Save the session to persist the changes

            # Add a success message
            messages.success(request, 'Entry added temporarily.')
            print(request.session['tempAdd'])

            # Redirect to create_entry to show the updated form
            return redirect('create_entry')
    
    else:
        form = UserEntryForm()
        temp_add = request.session.get('tempAdd', [])
        
        for entry in temp_add:
            if 'arrival_date' in entry:
                # Convert ISO string to datetime object
                if isinstance(entry['arrival_date'], str):  # Check if it's still a string
                    try:
                        entry['arrival_date'] = datetime.fromisoformat(entry['arrival_date'])
                    except ValueError:
                        pass  # Handle invalid ISO format if needed

        return render(request, 'create_entry.html', {'form': form, 'tempAdd': temp_add})


  
def create_entry(request):
    tempAdd = request.session.get('tempAdd', [])
    
    for entry in tempAdd:
        if 'arrival_date' in entry:
            # Format the arrival_date for template rendering
            try:
                # Convert ISO string to datetime
                if isinstance(entry['arrival_date'], str):
                    entry['arrival_date'] = datetime.fromisoformat(entry['arrival_date'])
            except ValueError:
                pass  # Handle invalid datetime format gracefully

    form = UserEntryForm(request.POST or None, tempAdd=tempAdd)
    
    return render(request, 'create_entry.html', {'form': form, 'tempAdd': tempAdd})



def clear_session(request):
    if 'tempAdd' in request.session:
        del request.session['tempAdd']
    return redirect('create_entry')




def removeEntry(request, index):
    # Get the list from session
    temp_add = request.session.get('tempAdd', [])

    # Remove the entry at the specified index
    if 0 <= index < len(temp_add):
        temp_add.pop(index)

    # Save the session to persist the changes
    request.session['tempAdd'] = temp_add
    request.session.modified = True

    if not temp_add:
        # If empty, redirect to the clear-session view
        return redirect('clear-session')

    # Add a success message
    messages.success(request, 'Entry removed successfully.')

    return redirect('temp-add')


def qr_code_list(request):
    # Use select_related to optimize the query and fetch related UserEntry
    qr_codes = QRCode.objects.select_related('entry_id').all()
    return render(request, 'qr_code_list.html', {'qr_codes': qr_codes})

def qr_scan(request, qr_data):
    try:
        # Retrieve the QRCode object based on the entry ID (from `qr_data`)
        qr_code = get_object_or_404(QRCode, entry_id=qr_data)

        # Check if the QR code status is not 0 (unscanned)
        if qr_code.status != 0:
            # If already claimed, return a different page
            return render(request, 'qr_invalid.html', {
                'error': 'This QR code has already been claimed or is invalid.'
            })

        # If QR code is valid and unscanned, proceed to show the claim voucher button
        return render(request, 'qr_scan_result.html', {
            'claim_voucher_button': True
        })

    except Exception as e:
        # Return an error message if there's an issue
        return render(request, 'invalid.html', {'error': 'Entry not found or invalid QR code.'})

    

def scan_qr(request):
    return render(request, 'scan_qr.html')


def check_qr_status(request, user_data_id):
    try:
        qr_code = QRCode.objects.get(entry_id=user_data_id)
        return JsonResponse({'status': qr_code.status})  # Return the status of the QR code
    except QRCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'QR Code not found.'}, status=404)

def entrance(request):
    return render(request, 'entrance.html')
    
@csrf_exempt
@require_POST
def mark_as_pending(request, user_entry_id):
    logger.info(f'Marking QR Code as Pending for User Entry ID: {user_entry_id}')
    
    try:
        # Fetch the QRCode object within a transaction
        with transaction.atomic():
            # Get the QRCode related to the UserEntry, assuming one QRCode per UserEntry
            qr_code = QRCode.objects.select_for_update().get(entry_id=user_entry_id)
            
            # Check if the QR code is already pending or scanned
            if qr_code.status == 1:  # Assuming 1 indicates Pending
                logger.warning(f'QR Code for User Entry ID {user_entry_id} is already inside.')
                return JsonResponse({'status': 'error', 'message': 'This person is already inside.'})
            
            if qr_code.status == 2:  # Assuming 2 indicates Claimed
                logger.warning(f'QR Code for User Entry ID {user_entry_id} is already claimed.')
                return JsonResponse({'status': 'error', 'message': 'This QR code is already claimed.'})
            if qr_code.status == 0:
                qr_code.status = 1
            qr_code.save()

        logger.info(f'QR Code for User Entry ID {user_entry_id} marked as Pending successfully.')
        return JsonResponse({'status': 'success', 'message': 'QR Code marked as Pending.'})
    
    except QRCode.DoesNotExist:
        logger.error(f'QRCode not found for User Entry ID: {user_entry_id}.')
        return JsonResponse({'status': 'error', 'message': 'QRCode not found for the specified user entry.'})
    
    except Exception as e:
        logger.error(f'An unexpected error occurred: {e}')
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'})




@csrf_exempt
@require_POST
def mark_as_scanned(request, user_entry_id):
    logger.info(f'Marking QR Code as scanned for User Entry ID: {user_entry_id}')
    
    try:
        # Fetch the QRCode object within a transaction
        with transaction.atomic():
            # Get the QRCode related to the UserEntry, assuming one QRCode per UserEntry
            qr_code = QRCode.objects.select_for_update().get(entry_id=user_entry_id)
            
            # Check if the QR code status is 0 (unscanned) or 2 (pending)
            if qr_code.status not in [0, 1]:  # If the status is neither 0 nor 2, it can't be scanned
                logger.warning(f'QR Code for User Entry ID {user_entry_id} is not available for scanning (status: {qr_code.status}).')
                return JsonResponse({'status': 'error', 'message': 'This voucher is already claimed.'})

            # Mark the QR code as scanned
            if qr_code.status == 1:
                qr_code.status = 2  # Mark as scanned
                qr_code.save()


        logger.info(f'QR Code for User Entry ID {user_entry_id} marked as scanned successfully.')
        return JsonResponse({'status': 'success', 'message': 'QR Code marked as scanned.'})
    
    except QRCode.DoesNotExist:
        logger.error(f'QRCode not found for User Entry ID: {user_entry_id}.')
        return JsonResponse({'status': 'error', 'message': 'QRCode not found for the specified user entry.'})
    
    except Exception as e:
        logger.error(f'An unexpected error occurred: {e}')
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'})
