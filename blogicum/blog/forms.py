from blog.models import Comment, Post, User
from django import forms


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%d/%m/%Y %H:%M',
                attrs={'type': 'datetime-local'}
            )
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email'
        )
