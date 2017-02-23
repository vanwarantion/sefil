from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import validate_comma_separated_integer_list
from django.db.models.aggregates import Sum
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse

from datetime import datetime, timedelta
import uuid, re

# Max days for next_date()
NEXT_DATE_MAX = 90

def unique_slugify(instance, value, slug_field_name='slug', queryset=None,
                   slug_separator='-'):
    """
    Calculates and stores a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.

    Source: https://djangosnippets.org/snippets/690/
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug, limiting its length if necessary.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create the queryset if one wasn't explicitly provided and exclude the
    # current instance from the queryset.
    if queryset is None:
        queryset = instance.__class__._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, at '-2' to the end and try again
    # (then '-3', etc).
    next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = '%s%s' % (slug_separator, next)
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[:slug_len-len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = '%s%s' % (slug, end)
        next += 1

    setattr(instance, slug_field.attname, slug)

def _slug_strip(value, separator='-'):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.

    Source: https://djangosnippets.org/snippets/690/
    """
    separator = separator or ''
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % re.escape(separator)
    # Remove multiple instances and if an alternate separator is provided,
    # replace the default '-' separator.
    if separator != re_sep:
        value = re.sub('%s+' % re_sep, separator, value)
    # Remove separator from the beginning and end of the slug.
    if separator:
        if separator != '-':
            re_sep = re.escape(separator)
        value = re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)
    return value

class FinanceItem(models.Model):
    creation = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    deletion = models.DateTimeField(verbose_name="Deleted At", blank=True, null=True, editable=False)
    slug = models.SlugField(blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            unique_slugify(self, uuid.uuid4())
        super(FinanceItem, self).save(**kwargs)

class MoneyFlow(FinanceItem):
    FlowTypes = (
        (10, 'In'),
        (20, 'Out'),
    )
    user = models.ForeignKey(User, verbose_name="Django User relation")
    label = models.CharField(max_length=255, verbose_name='label')
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    begins_at = models.DateField(verbose_name="Transactions begin at", default=datetime.now)
    begins_at.editable = True
    ends_at = models.DateField(verbose_name="Transactions end at", null=True, blank=True)
    flow_type = models.PositiveSmallIntegerField(default=20, verbose_name="Flow Type", choices=FlowTypes)

    def __unicode__(self):
        return u"%d:%s (%s) %s" % (self.id, str(self.amount), self.label, self.get_flow_type_display())

    def get_absolute_url(self):
        return reverse('f_flow_view', args=[str(self.slug)])

    def text_description(self):
        def get_sch_text():
            if hasattr(self, 'flowschedule'):
                return "with schedule"
            return "without schedule"
        return u"%s %s %s" % (format(self.amount, ".2f"), self.get_flow_type_display(), get_sch_text())

    def balance(self):
        multiplier = 1
        if self.flow_type == 20:
            multiplier = -1
        transactions_total = self.financial_transaction_set.aggregate(Sum('amount'))['amount__sum'] or 0
        if self.ends_at:
            # If scheduled: Return existing balance - estimated remaining
            if self.flowschedule:
                return 999.99
            # If due date: Return existing balance
            return (self.amount - transactions_total) * multiplier

        return transactions_total * multiplier

class FlowSchedule(models.Model):
    flow = models.OneToOneField('MoneyFlow', verbose_name="Related Flow")
    dom = models.CharField(
        verbose_name="Day Of The Month",
        help_text="Single integer or a comma separated list of integers",
        validators=[validate_comma_separated_integer_list],
        max_length=100,
        default='0,'
    )
    moy = models.CharField(
        verbose_name="Month Of The Year",
        help_text="Single integer or a comma separated list of integers",
        validators=[validate_comma_separated_integer_list],
        max_length=100,
        default='0,'
    )
    dow = models.CharField(
        verbose_name="Day Of The Week",
        help_text="Single integer or a comma separated list of integers",
        validators=[validate_comma_separated_integer_list],
        max_length=100,
        default='0,'
    )

    def _int_list(self, v):
        # Convert comma separated list into int list [1,2,3,etc]
        return [int(x) for x in v.split(',')]

    def _dom(self):
        dom_list = self._int_list(self.dom)

    def _valid_date(self, d):
        """
        Check if given date is in schedule
        """
        dom_list = self._int_list(self.dom)
        if 0 in dom_list:
            dom_list = [x for x in range(1, 32)]
        moy_list = self._int_list(self.moy)
        if 0 in moy_list:
            moy_list = [x for x in range(1, 13)]
        dow_list = self._int_list(self.dow)
        if 0 in dow_list:
            dow_list = [x for x in range(1, 8)]

        if d.month not in moy_list:
            # print "Month:", d.month, moy_list
            return False

        if d.day not in dom_list:
            # print "Day:", d.day, dom_list
            return False

        if d.isoweekday() not in dow_list:
            # print "Weekday:", d.isoweekday(), dow_list
            return False

        return True

    def get_next_date(self, start_date = None):
        if start_date:
            current_date = start_date
        else:
            current_date = datetime.now().date()
        final_date = self.flow.ends_at or current_date + timedelta(days=NEXT_DATE_MAX)
        while current_date < final_date:
            if self._valid_date(current_date) == True:
                return current_date
            current_date = current_date + timedelta(days=1)

class financial_transaction(FinanceItem):
    flow = models.ForeignKey('MoneyFlow', verbose_name="Money Flow")
    created_at = models.DateTimeField(default=datetime.now, verbose_name="Entered At")
    created_at.editable=True
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Enter 0 for default amount of selected money flow.")

    class Meta:
        verbose_name = "Financial Transaction"
        ordering = ['-created_at']

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # Default amount is flow amount
        if self.amount == 0:
            self.amount = self.flow.amount
        super(financial_transaction, self).save(force_insert, force_update, using, update_fields)

    def get_absolute_url(self):
        return reverse('f_transaction_edit', args=[str(self.slug)])

class BalancedAccount(FinanceItem):
    label = models.CharField(max_length=255, verbose_name='label')
    flows = models.ManyToManyField('MoneyFlow')

    def flows_positive(self):
        return self.flows.filter(flow_type=10)

    def flows_negative(self):
        return self.flows.filter(flow_type=20)

    def balance(self):
        positive_transactions = financial_transaction.objects.filter(flow__in=self.flows_positive())
        negative_transactions = financial_transaction.objects.filter(flow__in=self.flows_negative())
        positive_total = positive_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        negative_total = negative_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        negative_total = negative_total * -1
        return positive_total + negative_total