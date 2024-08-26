from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate


User = get_user_model()

# User registration form
class CustomUserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['fullname', 'username', 'phone', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].required = False
        self.fields['comment'].required = False

    def clean_fullname(self):
        getName = self.cleaned_data['fullname'].strip()
        fullname = ' '.join(word.capitalize() for word in getName.split())
        return fullname

    def clean_username(self):
        username = self.cleaned_data['username'].strip().capitalize()
        if len(username) < 5:
            raise forms.ValidationError("Username should be atleast 5 alphabets long.")
        if not username.isalpha():
            raise forms.ValidationError("Username should contain only alphabets A-Z.")
        if self.instance and self.instance.pk:
            if User.objects.filter(username=username, deleted=False).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("This username is already used by another user.")
        else:
            if User.objects.filter(username=username, deleted=False).exists():
                raise forms.ValidationError("This username is already used by another user.")
        return username
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone').strip()
        if phone and not phone.isdigit():
            raise forms.ValidationError("Please use a 10-digit phone number.")
        if phone and len(phone) != 10:
            raise forms.ValidationError("Please use a 10-digit phone number.")
        if phone and self.instance and self.instance.pk:
            if User.objects.filter(phone=phone, deleted=False).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("This phone is already used by another user.")
        else:
            if phone and User.objects.filter(phone=phone, deleted=False).exists():
                raise forms.ValidationError("This phone is already used by another user.")
        return phone
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        return None if comment in ("", "-") else comment

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data['username'].strip().upper()
        user.set_password(password)
        if commit:
            user.save()
        return user
    
    


# User login form
class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Incorrect username or password.")
            if user.blocked:
                raise forms.ValidationError("Account blocked, contact your admin.")
            if user.deleted:
                raise forms.ValidationError("Invalid account, contact your admin.")
        return self.cleaned_data
