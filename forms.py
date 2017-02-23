from django.forms import ModelForm, MultipleChoiceField, inlineformset_factory, HiddenInput, SelectMultiple
from django.utils.datastructures import MultiValueDict
from django.core.exceptions import ValidationError

from models import *

class SelectIntList(SelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        """
        Convert comma separated integer list and return list
        """
        render_val = []
        if value:
            render_val = [int(x) for x in value.split(',')]
        # TODO: Return a compact table instead of this
        return super(SelectIntList, self).render(name, render_val, attrs, choices)

    def value_from_datadict(self, data, files, name):
        """
        Convert selection list and Return comma separated integer list
        """
        if isinstance(data, MultiValueDict):
            return ','.join(map(str, data.getlist(name)))
        return data.get(name)

class MultiIntField(MultipleChoiceField):

    def to_python(self, value):
        if not value:
            raise ValidationError('At least one item must be selected', code='invalid_list')
        try:
            mylist = [int(x) for x in value.split(',')]
        except ValueError:
            return '0,'
        if not isinstance(mylist, (list, tuple)):
            raise ValidationError('Invalid List', code='invalid_list')
        return value

    def validate(self, value):
        if self.required and not value:
            raise ValidationError('Selection Required', code='required')

class BootstrapModelForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        for i in self.fields.keys():
            self.fields[i].widget.attrs.update({'class' : 'form-control'})
            if isinstance(self.fields[i], MultiIntField) == True:
                self.fields[i].widget.attrs.update({'class' : 'form-control fin-checkbox'})

class schedule_admin_form(BootstrapModelForm):
    dom_opts = [(0, "ALL (Overrides other selections)")] + [(x, str(x)) for x in range(1, 32)]
    dom = MultiIntField(widget=SelectIntList, choices=dom_opts, label="Days Of Month", help_text="Select Days", initial="0")
    moy_opts = (
        ('0', "ALL (Overrides other selections)"),
        ('1', "Jan"),
        ('2', "Feb"),
        ('3', "Mar"),
        ('4', "Apr"),
        ('5', "May"),
        ('6', "Jun"),
        ('7', "Jul"),
        ('8', "Aug"),
        ('9', "Sep"),
        ('10', "Oct"),
        ('11', "Nov"),
        ('12', "Dec"),
    )
    moy = MultiIntField(widget=SelectIntList, choices=moy_opts, label="Months Of Year", help_text="Select Months", initial="0")
    dow_opts = (
        (0, "ALL (Overrides other selections)"),
        (1, "Mon"),
        (2, "Tue"),
        (3, "Wed"),
        (4, "Thu"),
        (5, "Fri"),
        (6, "Sat"),
        (7, "Sun"),
    )
    dow = MultiIntField(widget=SelectIntList, choices=dow_opts, label="Weekdays", help_text="Select Weekdays", initial="3")

    class Meta:
        model = FlowSchedule
        fields = ['flow', 'dom', 'moy', 'dow']

class flows_admin_form(BootstrapModelForm):
    class Meta:
        model = MoneyFlow
        fields = ['user', 'label', 'amount', 'flow_type', 'begins_at', 'ends_at']

    def clean_user(self):
        if self.django_user:
            return self.django_user
        else:
            return self.cleaned_data['user']

    def __init__(self, *args, **kwargs):
        self.django_user = kwargs.pop('user', None)
        super(flows_admin_form, self).__init__(*args, **kwargs)
        if self.django_user:
            self.fields['user'].widget = HiddenInput()
            self.fields['user'].required = False
        if self.instance.pk:
            self.fields['user'].widget = HiddenInput()

class transaction_form(BootstrapModelForm):
    class Meta:
        model = financial_transaction
        fields = ['flow', 'amount', 'created_at']

    def __init__(self, *args, **kwargs):
        self.flow = kwargs.pop('flow', None)
        super(transaction_form, self).__init__(*args, **kwargs)
        if self.flow:
            self.fields['flow'].initial = self.flow
            self.fields['flow'].widget = HiddenInput()
            self.fields['flow'].required = False
        if self.instance.pk is None:
            self.fields['created_at'].widget = HiddenInput()
            self.fields['created_at'].required = False

flow_inline_formset = inlineformset_factory(MoneyFlow, FlowSchedule, form=schedule_admin_form, extra=1, can_delete=False)