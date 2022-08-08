import shutil
import tempfile
from http import HTTPStatus
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Post, Group, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
test_image_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded_image = SimpleUploadedFile(
            name='image.gif',
            content=test_image_gif,
            content_type='image/gif'
        )
        cls.follower = User.objects.create_user(username='follower')
        cls.user = User.objects.create_user(username='Name1')
        cls.group = Group.objects.create(
            title='Текстовый заголовок',
            slug='test-slug',
            description='текстовый текст',
        )
        cls.post = Post.objects.create(
            image=cls.uploaded_image,
            text='какой-то текст',
            author=cls.user,
            group=cls.group,
        )
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.follower,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'Name1'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста главной страницы
    def test_index_page_show_correct_context(self):
        """Шаблон index передает список постов."""
        self.uploaded_image.seek(0)
        response = self.authorized_client.get(reverse('posts:index'))
        cache.clear()
        posts_list = len(response.context['page_obj'])
        self.assertEqual(posts_list, Post.objects.count())

    # Проверка словаря контекста на странице всех записей группы
    def test_group_posts_show_correct_context(self):
        """Шаблон group_posts передает список постов,
        отфильтрованных по группе."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={
                'slug': self.group.slug
            })
        )
        form_fields = {
            response.context['group'].title: 'Текстовый заголовок',
            response.context['group'].slug: 'test-slug',
            response.context['group'].description: 'текстовый текст',
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    # Проверка словаря контекста на странице постов пользователя в профайле
    def test_profile_show_correct_context(self):
        """Шаблон profile передает список постов,
        отфильтрованных по пользователю-автору."""
        self.uploaded_image.seek(0)
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': PostPagesTests.user})
        )
        self.assertEqual(
            response.context['author'].username, 'Name1'
        )

    # Проверка словаря контекста на странице конкретного поста
    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail передает 1 пост автора."""
        self.uploaded_image.seek(0)
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostPagesTests.post.id
            })
        )
        self.assertEqual(response.context['post'].id, self.post.id)

    def test_posts_edit_show_correct_context(self):
        """Шаблон create (edit) сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': PostPagesTests.post.id
            })
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
    # Проверка словаря контекста на странице создания поста

    def test_create_new_post_show_correct_context(self):
        """Шаблон crtate (edit) передает форму  написания поста автора."""
        context = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for reverse_page in context:
            self.uploaded_image.seek(0)
            response = self.authorized_client.get(reverse_page)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_get_the_right_group(self):
        '''Созданный пост не поподает в другую группу.'''
        self.uploaded_image.seek(0)
        PostPagesTests.post_2 = Post.objects.create(
            group=PostPagesTests.group,
            author=PostPagesTests.user,
            text='Текстовый пост 2',
        )
        group_2 = Group.objects.create(
            title='Текстовый заголовок 2',
            slug='test-slug_2',
            description='текстовый текст 2',
        )
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': group_2.slug}
        ))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_image_show_correct_context(self):
        '''Картинка передается на странице в правильном контексе.'''
        urls_next = [
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': 'Name1'}),
            reverse('posts:index')
        ]
        for urls in urls_next:
            response = self.authorized_client.get(urls)
            cache.clear()
            tested_post = response.context['page_obj'][0]
            self.assertEqual(tested_post.image, self.post.image)
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostPagesTests.post.id
            })
        )
        self.assertEqual(tested_post.image, self.post.image)

    def test_cache_index_page(self):
        """Проверяем что главная страница кешируется на 20 секунд."""
        response_one = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            text='Текст тестировки кэша',
            author=self.user,
        )
        response_two = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_one.content, response_two.content)
        cache.clear()
        response_three = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_one.content, response_three.content)

    def test_user_can_follow_to_author(self):
        """Тест подписки на автора (posts):
        Проверка возможности подписки авторизованного пользователя на автора.
        """
        response = self.follower_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.post.author}
        ))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.post.author
            ).exists()
        )

    def test_follower_can_unfollow_from_author(self):
        """Тест отписки от автора (posts):
        Проверка возможности отписки авторизованного пользователя от автора.
        """
        self.follower_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.post.author}
        ))
        response = self.follower_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.post.author}
        ))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.post.author
            ).exists()
        )

    def test_user_can_follow_to_himself(self):
        """Тест: Нельзя подписаться на себя (posts)."""
        response = self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.post.author}
        ))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.post.author
            ).exists()
        )
        assert self.user.follower.count() == 0

    def test_new_posts_in_follow_list(self):
        """Тест появления нового поста у подписанных пользователей (posts).
        Проверка появления новой записи пользователя в ленте тех,
        кто на него подписан.
        """
        response = self.follower_client.get(reverse('posts:follow_index'))
        context = response.context['page_obj'].object_list
        self.assertIn(self.post, context)

    def test_new_posts_not_in_follow_list(self):
        """Тест отсутствия нового поста у неподписанных пользователей (posts).
        Проверка отсутствия появления новой записи пользователя в ленте тех,
        кто на него не подписан.
        """
        self.follower_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.post.author}
        ))
        response = self.follower_client.get(reverse('posts:follow_index'))
        context = response.context['page_obj'].object_list
        self.assertNotIn(self.post, context)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Запись группы.
        cls.user = User.objects.create_user(username='auth')
        # Запись поста бд.
        cls.group = Group.objects.create(
            title='Текстовая группа',
            slug='test-slug',
            description='текстовый текст',
        )
        cls.posts = Post.objects.bulk_create([
            Post(
                author=cls.user,
                text=f'Тестовый пост{i}',
                group=cls.group,
            )
            for i in range(1, 17)
        ])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_page_contains(self):
        '''Paginator исправен.'''
        all_posts = len(PaginatorViewsTest.posts)
        fist_posts = settings.CONSTANT
        number_list = all_posts // settings.CONSTANT
        second_posts = all_posts % settings.CONSTANT
        quantity_page = number_list + 1
        check_pagination = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        ]
        for url in check_pagination:
            response = self.client.get(url, {'page': quantity_page})
            cache.clear()
            number_posts_on_page = len(response.context['page_obj'])
            # Проверка 1 страницы.
            self.assertEqual(len(self.guest_client.get(
                url).context['page_obj']), fist_posts
            )
            # Проверка последний страницы.
            self.assertEqual(number_posts_on_page, second_posts)
