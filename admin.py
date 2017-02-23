from django.contrib import admin

# Register your models here.
from forms import *

class schedule_admin(admin.StackedInline):
    model = FlowSchedule
    form = schedule_admin_form
    fk_name = 'flow'
    extra = 0

class flows_admin(admin.ModelAdmin):
    model = MoneyFlow
    form = flows_admin_form
    inlines = [schedule_admin]
    list_display = ['label', 'amount', 'flow_type', 'dom_display', 'moy_display', 'dow_display', 'begins_at', 'ends_at', 'balance_display']
    fields = ['user', 'label', 'amount', 'flow_type', 'begins_at', 'ends_at', 'slug']
    readonly_fields = ['slug']

    def dom_display(self, obj):
        sch = obj.flowschedule
        if sch:
            return obj.flowschedule.dom
    dom_display.allow_tags = True
    dom_display.short_description = "Days Of Month"

    def moy_display(self, obj):
        sch = obj.flowschedule
        if sch:
            return obj.flowschedule.moy
    moy_display.allow_tags = True
    moy_display.short_description = "Months"

    def dow_display(self, obj):
        sch = obj.flowschedule
        if sch:
            return obj.flowschedule.dow
    dow_display.allow_tags = True
    dow_display.short_description = "Weekdays"

    def balance_display(self, obj):
        return obj.balance()
    balance_display.allow_tags = True
    balance_display.short_description = "Balance"

admin.site.register(MoneyFlow, flows_admin)


class transactions_admin(admin.ModelAdmin):
    model = financial_transaction
    list_display = ['flow', 'created_at', 'amount']
    fields = ['flow', 'created_at', 'amount']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return ['created_at']

admin.site.register(financial_transaction, transactions_admin)

class accounts_admin(admin.ModelAdmin):
    model = BalancedAccount
    list_display = ['label', 'balance_display']

    def balance_display(self, obj):
        return obj.balance()
    balance_display.allow_tags = True
    balance_display.short_description = "Balance"

admin.site.register(BalancedAccount, accounts_admin)