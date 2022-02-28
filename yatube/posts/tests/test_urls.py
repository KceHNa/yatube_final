from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.author = User.objects.create_user(username='auth_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста',
        )
        cls.post_url = f'/posts/{cls.post.id}/'
        cls.post_url_edit = f'/posts/{cls.post.id}/edit/'
        cls.comment_url = f'/posts/{cls.post.id}/comment/'
        cls.public_urls = (
            ('/', 'posts/index.html'),
            ('/about/author/', 'about/author.html'),
            ('/about/tech/', 'about/tech.html'),
            ('/group/test-slug/', 'posts/group_list.html'),
            ('/profile/auth_user/', 'posts/profile.html'),
            (cls.post_url, 'posts/post_detail.html'),
        )
        cls.private_urls = (
            ('/create/', 'posts/create_post.html'),
            (cls.post_url_edit, 'posts/create_post.html'),
            ('/follow/', 'posts/follow.html'),
        )

    def setUp(self):
        """Создание гостя и авторизованного пользователя, автора."""
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_urls_work(self):
        """Проверяем url доступные любому пользователю."""
        for url, _ in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauth_user_cannot_access_private_urls(self):
        """Проверяем недоступные url для неавторизованных users."""
        login_url = '/auth/login/'
        for url, _ in self.private_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                target_url = f'{login_url}?next={url}'
                self.assertRedirects(response, target_url)

    def test_authenticated_author_can_access_private_urls(self):
        """Проверяем недоступные url для авторизованного автора."""
        for url, _ in self.private_urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_use_correct_templates(self):
        """Проверяем шаблоны для всех users."""
        for url, template in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_private_urls_use_correct_template_for_post_author(self):
        """Проверяем шаблоны для авторов."""
        for url, template in self.private_urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_guest_user_cannot_edit_post(self):
        """Проверка: пост редактирует пост только автор."""
        response = self.authorized_client.get(self.post_url_edit)
        self.assertRedirects(response, self.post_url)

    def test_guest_user_cannot_add_comment(self):
        """Проверка: комментарий добавляет
        только авторизованный пользователь."""
        response = self.guest_client.get(self.comment_url)
        target_url = f'/auth/login/?next={self.comment_url}'
        self.assertRedirects(response, target_url)

    def test_server_responds_404_for_unexisting_page(self):
        response = self.authorized_client.get('/unexisting-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_authorized_user_follow_page(self):
        """Проверка: только авторизованному пользователю доступна
        страничка подписок."""
        response = self.guest_client.get('/follow/')
        target_url = '/auth/login/?next=/follow/'
        self.assertRedirects(response, target_url)
