import datetime
import re
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import User, WithdrawalRequest

# Tron base58check addresses: 'T' + 33 base58 characters (no 0/O/I/l).
TRC20_ADDRESS_RE = re.compile(r'^T[1-9A-HJ-NP-Za-km-z]{33}$')


def validate_trc20_address(value: str) -> str:
    if not TRC20_ADDRESS_RE.match(value):
        raise forms.ValidationError('Enter a valid USDT-TRC20 (Tron) address.')
    return value


class EmailSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='You must be 18 or older to play.',
    )

    class Meta:
        model = User
        fields = ('email', 'birth_date', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        today = timezone.localdate()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise forms.ValidationError('You must be 18 or older to create an OnlyBall account.')
        if birth_date > today:
            raise forms.ValidationError('Enter a valid birth date.')
        return birth_date

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.birth_date = self.cleaned_data['birth_date']
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EmailLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class BuyBallForm(forms.Form):
    usdt_amount = forms.DecimalField(min_value=Decimal('0.01'), max_digits=18, decimal_places=6)


class DepositForm(forms.Form):
    usdt_amount = forms.DecimalField(
        min_value=Decimal('10'), max_digits=18, decimal_places=6,
        widget=forms.NumberInput(attrs={'min': '10', 'step': '0.01'}),
        error_messages={'min_value': 'Minimum deposit is $10 USDT.'},
    )


# Tron transaction hashes are 64 hex characters.
TX_HASH_RE = re.compile(r'^[0-9a-fA-F]{64}$')


class ManualDepositForm(forms.Form):
    usdt_amount = forms.DecimalField(
        min_value=Decimal('10'), max_digits=18, decimal_places=6,
        widget=forms.NumberInput(attrs={'min': '10', 'step': '0.01'}),
        error_messages={'min_value': 'Minimum deposit is $10 USDT.'},
    )
    tx_hash = forms.CharField(
        max_length=128,
        help_text='The transaction hash from your USDT-TRC20 transfer, so an admin can verify it.',
    )

    def clean_tx_hash(self):
        value = self.cleaned_data['tx_hash'].strip()
        if not TX_HASH_RE.match(value):
            raise forms.ValidationError('Enter a valid 64-character Tron transaction hash.')
        return value


class WithdrawalForm(forms.Form):
    address = forms.CharField(max_length=64)
    amount_usdt = forms.DecimalField(min_value=Decimal('0.01'), max_digits=18, decimal_places=6)

    class Meta:
        model = WithdrawalRequest
        fields = ('address', 'amount_usdt')

    def clean_address(self):
        return validate_trc20_address(self.cleaned_data['address'])


class PayoutAddressForm(forms.Form):
    usdt_trc20_payout_address = forms.CharField(max_length=64, required=False)

    def clean_usdt_trc20_payout_address(self):
        value = self.cleaned_data['usdt_trc20_payout_address']
        return validate_trc20_address(value) if value else value


class SelfExclusionForm(forms.Form):
    DURATION_CHOICES = [(7, '7 days'), (30, '30 days'), (90, '90 days')]
    days = forms.TypedChoiceField(choices=DURATION_CHOICES, coerce=int)


class DepositCapForm(forms.Form):
    weekly_deposit_cap_usdt = forms.DecimalField(
        required=False, min_value=Decimal('0'), max_digits=18, decimal_places=6,
        help_text='Leave blank to remove your personal weekly deposit cap.',
    )
