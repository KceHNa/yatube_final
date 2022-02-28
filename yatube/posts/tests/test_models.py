from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Длинный текст поста тестовой группы!!!',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.user,
        )

    def test_post_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        # класса Post — первые пятнадцать символов поста: **post.text[:15];
        # для класса Group — название группы
        self.assertEqual(str(self.post), self.post.text[:15])
        self.assertEqual(str(self.group), self.group.title)
        self.assertEqual(str(self.comment), self.comment.text)

    def test_post_model_help_text(self):
        """help_text полей совпадает с ожидаемым."""
        field_dict = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Загрузите картинку',
        }
        for field, text_field in field_dict.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    text_field,
                    msg='Ошибка в поле'
                )

    def test_group_model_verbose_name(self):
        """verbose_name полей совпадает с ожидаемым."""
        field_dict = {
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, text_field in field_dict.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    text_field,
                    msg='Ошибка в поле'
                )


class CommentModelTest(PostModelTest):
    def test_comment_model_verbose_name(self):
        """verbose_name полей совпадает с ожидаемым."""
        field_dict = {
            'author': 'Автор',
            'text': 'Добавить комментарий',
            'created': 'Дата публикации',
        }
        for field, text_field in field_dict.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.comment._meta.get_field(field).verbose_name,
                    text_field,
                    msg='Ошибка в поле'
                )

    def test_comment_model_help_text(self):
        """help_text полей совпадает с ожидаемым."""
        field_dict = {
            'text': 'Оставьте свой комментарий под этим постом',
        }
        for field, text_field in field_dict.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.comment._meta.get_field(field).help_text,
                    text_field,
                    msg='Ошибка в поле'
                )

# class FollowModelTest(PostModelTest):
#     def test_follow_models_correct_constraints(self):
#         constraints = Follow.
