from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Создает форму-редактор постов."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': _('Редактор поста'),
            'group': _('Группа'),
            'image': 'Картинка',
        }
        help_texts = {
            'text': _('Введите текст поста'),
            'group': _('Выберите группу, к которой будет относиться пост'),
            'image': 'Картинка поста',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    # def clean_text(self):
    #     data = self.cleaned_data['text']
    #     if data == '':
    #         raise ValidationError
    #     return data
