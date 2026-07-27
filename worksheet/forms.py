from django.forms import ModelForm

from worksheet.models import Result


class ResultNoteForm(ModelForm):
    class Meta:
        model = Result
        fields = ["note"]
