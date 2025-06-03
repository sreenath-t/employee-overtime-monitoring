from django import forms

class UploadCSVForm(forms.Form):
    file = forms.FileField()    # is a form field used to handle file uploads through a form. It corresponds to a file input in HTML (<input type="file">). You typically use it in a Django Form or ModelForm when you want users to upload a file.