from django import forms

from projects.access import get_available_projects_for_user

from .models import Project, TimeSheetEntry


class TimeSheetEntryForm(forms.ModelForm):
    class Meta:
        model = TimeSheetEntry
        fields = ["project", "work_date", "hours", "description"]
        widgets = {
            "work_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the work completed"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None:
            project_queryset = Project.objects.filter(is_active=True)
        else:
            project_queryset = get_available_projects_for_user(user)

        if self.instance and self.instance.pk and self.instance.project_id:
            project_queryset = project_queryset | Project.objects.filter(pk=self.instance.project_id)

        self.fields["project"].queryset = project_queryset.distinct().order_by("name", "code")
