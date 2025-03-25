from django import forms

class WalletDepositForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2,
        min_value=1,  # Ensure a positive deposit amount
        label="Amount",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'})
    )
