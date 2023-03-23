from django.test import TestCase

from posts.models import Group, Post, User


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
            text='Тестовый постТестовый постТестовый постТестовый пост\
                Тестовый постТестовый постТестовый постТестовый пост\
                Тестовый постТестовый постТестовый пост\
                Тестовый постТестовый постТестовый пост\
                Тестовый постТестовый постТестовый пост',
        )

    def setUp(self):
        self.post = PostModelTest.post
        self.group = PostModelTest.group

    def test_models_have_correct_object_names(self):
        '''Проверяем, что у моделей корректно работает __str__.'''
        expected_models_names = (
            (str(self.post), self.post.text[:15]),
            (str(self.group), self.group.title)
        )
        for model_name, expected_model_name in expected_models_names:
            with self.subTest(model_name=model_name):
                self.assertEqual(model_name, expected_model_name)

    def test_model_post_have_verbose_name(self):
        '''Проверяем, что у моделей есть verbose_name'''
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for verbose, expected_verbose in field_verboses.items():
            with self.subTest(verbose=verbose):
                self.assertEqual(
                    self.post._meta.get_field(verbose).verbose_name,
                    expected_verbose
                )

    def test_model_post_help_text(self):
        '''Проверяем, что у моделей есть атрибут help_text'''
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for help_text, expected_text in field_help_texts.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(
                    self.post._meta.get_field(help_text).help_text,
                    expected_text
                )
