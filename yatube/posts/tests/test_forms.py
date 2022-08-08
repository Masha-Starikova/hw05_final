import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment
from ..forms import PostForm, CommentForm

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
class PostFormTest(TestCase):
    """Форма для создания поста."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded_image = SimpleUploadedFile(
            name='test_image.gif',
            content=test_image_gif,
            content_type='image/gif'
        )
        cls.uploaded_image_2 = SimpleUploadedFile(
            name='test_image2.gif',
            content=test_image_gif,
            content_type='image2/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст',
            image=cls.uploaded_image
        )
        cls.form = PostForm()
        cls.form = CommentForm
        cls.comment = Comment.objects.create(
            text='Текст комента',
            post=cls.post,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_forms_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'image': self.uploaded_image,
        }
        self.uploaded_image.seek(0)
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                text='Тестовый текст',
                image='posts/test_image.gif'
            ).exists()
        )

    def test_forms_edit_post(self):
        '''Валидная форма редактирует запись в Post.'''
        # Создаем пост.
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Я изменился',
            'image': self.uploaded_image_2,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        ),
            data=form_data,
            follow=True
        )
        # Проверяем редирект.
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        # Проверяем, не увеличилось ли число постов
        self.assertEqual(Post.objects.count(), post_count)
        # Проверяем что пост отредактирован
        self.assertTrue(
            Post.objects.filter(
                text='Я изменился',
                group=self.group,
                 image='posts/test_image2.gif'
            ).exists()
        )

    def test_comment_in_post_detail_page_show_exist(self):
        """Комментаррии после отправки отображаются на странице post_detail"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комента',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Текст комента'
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_comment_not_gost(self):
        '''Комментировать пост могут только авторизованные пользователи.'''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комента 2',
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Текст комента'
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comments_count)