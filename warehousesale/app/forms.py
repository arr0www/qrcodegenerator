# forms.py
from django import forms
from .models import UserEntry, Relative

class UserEntryForm(forms.ModelForm):
    # Fields for adding a Relative
    r_fname = forms.CharField(max_length=50, required=False, label="Employee First Name")
    r_lname = forms.CharField(max_length=50, required=False, label="Employee Last Name")
    r_department = forms.ChoiceField(
        choices=Relative._meta.get_field('r_department').choices,
        required=False,
        label="Department"
    )
    relationship = forms.ChoiceField(
        choices=UserEntry._meta.get_field('relationship').choices,
        required=True,
        label="Relationship"
    )
    arrival_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Arrival Date and Time"
    )

    class Meta:
        model = UserEntry
        fields = ['r_fname', 'r_lname', 'r_department', 'arrival_date', 'fname', 'lname', 'relationship']
        labels = {
            'fname': 'Relative First Name',
            'lname': 'Relative Last Name',
        }

    def __init__(self, *args, **kwargs):
        tempAdd = kwargs.pop('tempAdd', [])  # Get tempAdd from kwargs passed by the view
        super().__init__(*args, **kwargs)

        # Set default values from tempAdd (if it exists)
        if tempAdd:
            latest_data = tempAdd[-1]  # Use the latest entry from tempAdd
            self.fields['r_fname'].initial = latest_data.get('r_fname', '')
            self.fields['r_lname'].initial = latest_data.get('r_lname', '')
            self.fields['r_department'].initial = latest_data.get('r_department', '')