from .models import ExtraInfo
from django.forms import ModelForm

class ExtraInfoForm(ModelForm):
    """
    The fields on this form are derived from the ExtraInfo model in models.py.
    """
    def __init__(self, *args, **kwargs):
        super(ExtraInfoForm, self).__init__(*args, **kwargs)
        self.fields['organization'].error_messages = {
            "required": u"Please tell us the organization you are affiliated with."
        }
        self.fields['goals'].error_messages = {
            "required": u"Please tell us your goals for using HydroLearn (e.g., develop new content; use or customize existing content)"
        }
        self.fields['usage'].error_messages = {
            "required": u"Please tell us if you are a student or instructor"
        }

    class Meta(object):
        model = ExtraInfo
        fields = ('organization', 'usage', 'goals')
