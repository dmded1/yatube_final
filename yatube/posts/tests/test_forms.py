from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, User
from posts.tests.constants import PROFILE_URL, POST_CREATE_URL


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='unknown')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.TEST_ID = cls.post.id
        cls.POST_EDIT_URL = reverse('posts:post_edit', args={cls.TEST_ID})
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args={cls.TEST_ID})

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        '''При отправке валидной формы создания поста,
        создаётся новая запись в базе данных'''
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый пост'}
        response = self.authorized_client.post(
            POST_CREATE_URL, data=form_data, follow=True
        )
        self.assertRedirects(
            response, PROFILE_URL)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(self.post.text, 'Тестовый пост')
        self.assertEqual(self.post.author.username, self.user.username)
        self.assertEqual(self.post.group.title, self.group.title)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        '''При отправке валидной формы редактирования поста,
        происходит изменения поста с post_id в базе данных'''
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый пост', 'group': self.group.id}
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, self.POST_DETAIL_URL)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.post.text, 'Тестовый пост')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_not_create_guest_client(self):
        '''При отправке валидной формы редактирования поста,
        изменения не произойдёт, если пользователь не авторизован'''
        posts_count = Post.objects.count()
        form_data = {'text': 'Новый текст', 'group': self.group.id}
        response = self.guest_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text='Новый текст').exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)
