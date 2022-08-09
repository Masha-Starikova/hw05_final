from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

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
            text='Ж'*100,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        list_of_expected_values = {
            self.post: self.post.text[:15],
            self.group: self.group.title,
        }
        for instance, expected_value in list_of_expected_values.items():
            with self.subTest(expected_value=expected_value):
                self.assertEqual(
                    expected_value,
                    instance,
                    'Метод __str__ работает некорректно!'
                )
