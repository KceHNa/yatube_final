import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

User = get_user_model()
# Временную папка для медиа-файлов
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostManipulationFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_create_post(self):
        """Неавторизованный пользователь пытается создать запись."""
        form_data = {
            'text': 'УникальныйТекст',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('users:login') + '?next=/create/'
        )
        last_post = Post.objects.last()
        self.assertNotEqual(last_post.text, 'УникальныйТекст')

    def test_valid_form_post_create(self):
        """Создаем новый пост через форму post_create."""
        # Подсчитаем количество записей до
        post_count: int = Post.objects.count()
        form_data = {
            'text': 'Текст поста из формы',
            'group': self.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'auth_user'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_invalid_form_post_create(self):
        """Форма не прошла валидацию."""
        post_count: int = Post.objects.count()
        form_data = {
            'text': '',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        saved_post = Post.objects.count()
        self.assertEqual(saved_post, post_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_valid_form_post_edit(self):
        """Проверка: пост по id изменяется."""
        base_text = 'Новый текст тестового поста'
        form_data = {
            'group': self.group.pk,
            'text': base_text,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=self.post.pk)
        self.assertEqual(base_text, edited_post.text)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_user_add_comment(self):
        """Авторизованный пользоваль оставляет комментарий."""
        comments_count: int = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария под постом',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        last_comment = Comment.objects.latest('created')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(last_comment.text, form_data['text'])
        self.assertEqual(last_comment.author, self.user)
