import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import ImageFieldFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth_author')
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
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
        # Создаем 13 тестовых записей
        for post_index in range(0, 13):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый текст поста',
                group=cls.group,
            )
        cls.post_id = cls.post.id

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создание гостя и авторизованного пользователя."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': self.user})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post_id})
            ),
            'posts/create_post.html': (
                reverse('posts:post_edit', kwargs={'post_id': self.post_id})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        template_name = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for reverse_name in template_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object, self.post)
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.group, self.post.group)
                self.assertEqual(first_object.author, self.post.author)
                self.assertIsInstance(first_object.image, ImageFieldFile)

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.author.username, self.user.username)

    def test_profile_correct_context(self):
        """profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        author_object = response.context['author']
        self.assertEqual(author_object, self.post.author)

    def test_post_detail_correct_context(self):
        """post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )
        first_object = response.context['post']
        test_items = {
            first_object.text: self.post.text,
            first_object.author: self.post.author,
            first_object.group: self.post.group,
            first_object.id: self.post.id,
        }
        for context, value in test_items.items():
            with self.subTest(context=context):
                self.assertEqual(context, value)
        self.assertIsInstance(first_object.image, ImageFieldFile)

    def text_post_create_correct_context(self):
        """post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsNone(response.context.get('is_edit', None))

    def test_post_edit_correct_context(self):
        """Проверка: post_edit редактирует пост с правильным id."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id})
        )
        form_fied_text = response.context['form'].initial['text']
        self.assertEqual(form_fied_text, self.post.text)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertTrue(response.context['is_edit'])
        self.assertIsInstance(response.context['is_edit'], bool)

    def test_post_in_your_group(self):
        """Проверка: пост с группой попал с свою группу."""
        Group.objects.create(
            title='Неверная тестовая группа',
            slug='false-group',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'false-group'})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_authorized_user_follow(self):
        """Авторизованный пользователь может подписываться
        на авторов."""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.author,
        ).exists())

    def test_authorized_user_unfollow(self):
        """Авторизованный пользователь отписывается от автора."""
        Follow.objects.create(
            user=self.author,
            author=self.user
        )
        self.author_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.author})
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.author)
        )

    def test_follow_post_at_the_user(self):
        """Корректность работы ленты избранных авторов."""
        post = Post.objects.create(
            author=self.author,
            text='Текст поста в избранном',
        )
        # Проверяем, что в избранное пост не попал
        response = self.authorized_client.get('/follow/')
        self.assertEqual(len(response.context['page_obj']), 0)
        # Подписываемся на автора
        Follow.objects.create(
            author=self.author,
            user=self.user
        )
        # Проверяем попал ли пост в избранное
        response = self.authorized_client.get('/follow/')
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, post.text)


class TestPaginator(PostPagesTests):

    def test_paginator_pages(self):
        """Проверка: пагинатора первой и последней страницы"""
        # Считаем сколько должно быть постов всего
        total_post_all = Post.objects.count()
        group = Group.objects.get(slug='test-slug')
        total_group_post = group.posts.count()
        author = User.objects.get(username='auth_user')
        total_profile_post = author.posts.count()
        reverse_names = {
            reverse('posts:index'): total_post_all,
            (reverse('posts:group_list', kwargs={'slug': 'test-slug'})):
                total_group_post,
            (reverse('posts:profile', kwargs={'username': 'auth_user'})):
                total_profile_post,
        }
        for reverse_name, total_post in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                # Проверяем первую стр. (всего 13 постов)
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)
                # Проверяем вторую
                last_page = 2
                response = self.client.get(
                    reverse_name + f'?page={last_page}'
                )
                self.assertEqual(
                    len(response.context['page_obj']), total_post % 10
                )
