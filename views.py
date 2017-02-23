from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from extra_views import InlineFormSet, UpdateWithInlinesView, CreateWithInlinesView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404

from models import *
from forms import *


class sch_inline_x(InlineFormSet):
    model = FlowSchedule
    form_class = schedule_admin_form
    can_delete = False

@method_decorator(login_required, name='dispatch')
class edit_flow(UpdateWithInlinesView):
    template_name = 'form.html'
    success_url = reverse_lazy('f_home')
    pattern_name = 'f_flow_edit'
    model = MoneyFlow
    inlines = [sch_inline_x]
    form_class = flows_admin_form

@method_decorator(login_required, name='dispatch')
class new_flow(CreateWithInlinesView):
    template_name = 'form.html'
    success_url = reverse_lazy('f_home')
    pattern_name = 'f_flow_new'
    model = MoneyFlow
    inlines = [sch_inline_x]
    form_class = flows_admin_form

    def get_form_kwargs(self):
        rv = super(new_flow, self).get_form_kwargs()
        rv['user'] = self.request.user
        return rv

@method_decorator(login_required, name='dispatch')
class finances_view(ListView):
    template_name = 'main.html'
    model = MoneyFlow
    pattern_name = 'f_home'

    def get_queryset(self):
        return MoneyFlow.objects.filter(user=self.request.user)

@method_decorator(login_required, name='dispatch')
class view_flow(DetailView):
    template_name = 'flow.html'
    model = MoneyFlow
    pattern_name = 'f_flow_view'

@method_decorator(login_required, name='dispatch')
class new_transaction(CreateView):
    template_name = 'form.html'
    form_class = transaction_form
    model = financial_transaction
    pattern_name = 'f_flow_transaction'
    success_url = reverse_lazy('f_home')

    def get_form_kwargs(self):
        rv = super(new_transaction, self).get_form_kwargs()
        rv['flow'] = get_object_or_404(MoneyFlow, slug=self.kwargs['slug'])
        return rv

@method_decorator(login_required, name='dispatch')
class edit_transaction(UpdateView):
    template_name = 'form.html'
    form_class = transaction_form
    model = financial_transaction
    pattern_name = 'f_transaction_edit'
    success_url = reverse_lazy('f_home')

    def get_form_kwargs(self):
        rv = super(edit_transaction, self).get_form_kwargs()
        rv['flow'] = self.object.flow
        return rv

@method_decorator(login_required, name='dispatch')
class delete_transaction(DeleteView):
    template_name = 'form.html'
    model = financial_transaction
    pattern_name = 'f_transaction_delete'
    success_url = reverse_lazy('f_home')