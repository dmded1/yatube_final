from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from posts.models import Post, Group, User
from posts.tests.constants import (INDEX_URL, GROUP_POSTS_URL,
                                   PROFILE_URL, POST_CREATE_URL)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='unknown')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.TEST_ID = cls.post.id
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args={cls.TEST_ID})
        cls.POST_EDIT_URL = reverse('posts:post_edit', args={cls.TEST_ID})
        cls.urls = [
            INDEX_URL,
            GROUP_POSTS_URL,
            PROFILE_URL,
            cls.POST_DETAIL_URL,
        ]
        cls.template_names = {
            INDEX_URL: 'posts/index.html',
            GROUP_POSTS_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            cls.POST_DETAIL_URL: 'posts/post_detail.html',
            cls.POST_EDIT_URL: 'posts/create_post.html',
            POST_CREATE_URL: 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_are_available(self):
        '''Проверяет доступность страниц'''
        for address in self.urls:
            with self.subTest(address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_templates(self):
        '''Проверяем, что URL-адрес использует соответствующий шаблон.'''
        for url, template in self.template_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_only_for_author(self):
        '''Проверяем доступность страницы posts/post_id/edit/
        только для автора поста.'''
        self.user = User.objects.get(username=self.user)
        response = self.authorized_client.get(self.POST_EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_only_authorized_and_redirect_if_not(self):
        '''Проверяем доступность страницы создания поста /create/
        только для авторизованного пользователя.'''
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_unexisting_page(self):
        '''Страница /unexisting_page/ должна выдать ошибку,
        т.к. не существует.
        Используется кастомный шаблон для страницы 404'''
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
