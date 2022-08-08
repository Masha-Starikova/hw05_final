from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Post, Group
from django.core.cache import cache

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )

    def setUp(self):
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTest.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            f'/posts/{PostURLTest.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostURLTest.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_urls_at_desired_location(self):
        templates_url_names = {
            '/': 200,
            '/group/test_slug/': 200,
            f'/posts/{PostURLTest.post.id}/': 200,
            '/profile/TestUser/': 200,
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                cache.clear()
                self.assertEqual(response.status_code, template)

    def test_urls_redirect_anonymous(self):
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, 302)

    def test_urls_redirect_anonymous_gost(self):
        response = self.guest_client.get(
            f'/posts/{PostURLTest.post.id}/edit/'
        )
        self.assertEqual(response.status_code, 302)
