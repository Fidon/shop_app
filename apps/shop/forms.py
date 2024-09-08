from django import forms
from .models import Product


# new product registartion form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['names', 'qty', 'price', 'expiry', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expiry'].required = False
        self.fields['comment'].required = False
        self.fields['qty'].required = False

    def clean_names(self):
        names = self.cleaned_data.get('names').strip()
        if len(names) < 3:
            raise forms.ValidationError("Product name is too short.")
        
        if self.instance and self.instance.pk:
            if Product.objects.filter(names=names, deleted=False).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Product name is already registered.")
        else:
            if Product.objects.filter(names=names, deleted=False).exists():
                raise forms.ValidationError("Product name is already registered.")
            
        return names

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        return None if comment in ("", "-") else comment