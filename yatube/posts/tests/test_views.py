import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django import forms

from posts.models import Comment, Follow, Group, Post, User
from posts.forms import PostForm
from posts.tests.constants import (INDEX_URL, GROUP_POSTS_URL,
                                   PROFILE_URL, POST_CREATE_URL,
                                   FOLLOW_INDEX_URL)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
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
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )
        cls.TEST_ID = cls.post.id
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args={cls.TEST_ID})
        cls.POST_EDIT_URL = reverse('posts:post_edit', args={cls.TEST_ID})
        cls.templates_pages_names = {
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
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        '''Проверяем, что страница использует соответствующий шаблон'''
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_index_show_correct_context(self):
        '''Проверяем корректность контекста при передаче в шаблон
        для страницы index'''
        response = self.guest_client.get(INDEX_URL)
        expected = list(Post.objects.select_related('author').all())
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_group_list_show_correct_context(self):
        '''Проверяем корректность контекста при передаче в шаблон
        для постов группы'''
        response = self.guest_client.get(GROUP_POSTS_URL)
        expected = list(Post.objects.filter(group_id=self.group.id))
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_profile_show_correct_context(self):
        '''Проверяем корректность контекста при передаче в шаблон
        для страницы-профайла пользователя'''
        response = self.guest_client.get(PROFILE_URL)
        expected = list(Post.objects.filter(author_id=self.user.id))
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_post_detail_show_correct_context(self):
        '''Проверяем корректность контекста при передаче в шаблон
        для страницы с детальным постом'''
        response = self.guest_client.get(self.POST_DETAIL_URL)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_post_edit_show_correct_context(self):
        '''Проверяем корректность контекста при передаче в шаблон
        для страницы редактирования поста'''
        response = self.authorized_client.get(self.POST_EDIT_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(name=field_name, type=field_type):
                form = response.context.get('form')
                self.assertIsInstance(form, PostForm)

    def test_post_create_show_correct_context(self):
        '''Проверяем корректность контекста при передаче в шаблон
        для страницы создания нового поста'''
        response = self.authorized_client.get(POST_CREATE_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(name=field_name, type=field_type):
                form = response.context['form']
                self.assertIsInstance(form, PostForm)

    def test_check_group_in_pages(self):
        '''Проверяем, что созданный пост отображается на всех страницах'''
        templates = {
            INDEX_URL: Post.objects.get(group=self.post.group),
            GROUP_POSTS_URL: Post.objects.get(group=self.post.group),
            PROFILE_URL: Post.objects.get(group=self.post.group),
        }
        for value, expected in templates.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        '''Проверяем, что пост не попал в группу,
        для которой не был предназначен.'''
        templates = {
            GROUP_POSTS_URL: Post.objects.exclude(group=self.post.group),
        }
        for value, expected in templates.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)

    def test_comments_only_for_authorized(self):
        '''Проверяем, что комментировать посты
        может только авторизованный пользователь'''
        response = self.guest_client.get(self.POST_DETAIL_URL)
        self.assertNotContains(response, self.comment)

    def test_new_comment_on_post_detail(self):
        '''После успешной отправки комментарий появляется на странице поста'''
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        self.assertContains(response, 'Тестовый комментарий')

    def test_check_cache_for_index_page(self):
        '''Проверяем кэш для главной страницы'''
        response = self.guest_client.get(INDEX_URL)
        first_view = response.content
        Post.objects.get(id=1).delete()
        response2 = self.guest_client.get(INDEX_URL)
        second_view = response2.content
        self.assertEqual(first_view, second_view)

    def test_following(self):
        '''Проверяем возможность подписаться/отписаться на автора
        и отображение поста'''
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response = self.authorized_client.get(FOLLOW_INDEX_URL)
        self.assertEqual(len(response.context['page_obj']), 1)

        # Создаём ещё одного авторизованного пользователя
        another_user = User.objects.create(username='another')
        self.authorized_client.force_login(another_user)
        response3 = self.authorized_client.get(FOLLOW_INDEX_URL)
        # Проверяем, что пост не появился у другого пользователя
        self.assertNotIn(self.post, response3.context['page_obj'])

        # Проверяем возможность отписаться
        Follow.objects.all().delete
        response2 = self.authorized_client.get(FOLLOW_INDEX_URL)
        self.assertEqual(len(response2.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
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
        posts = (Post(
            text=cls.post.text,
            group=cls.group,
            author=cls.user) for i in range(13))
        Post.objects.bulk_create(posts)[:10]
        cls.templates = {
            INDEX_URL: 'posts/index.html'
        }

    def test_index_contains_ten_posts(self):
        '''Проверяем, что страница индекс показывает
        только 10 постов на странице'''
        for reverse_name in self.templates.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PicturesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(PicturesTest, cls).setUpClass()
        cls.user = User.objects.create(username='unknown')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.TEST_ID = cls.post.id
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.TEST_ID}
        )
        cls.templates = (
            INDEX_URL, PROFILE_URL, GROUP_POSTS_URL
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_image_in_context_for_index_profile_group_list_pages(self):
        '''При выводе поста с картинкой изображение передаётся
        в словаре context на страницах index, profile, group_list'''
        for url in self.templates:
            with self.subTest(url):
                response = self.guest_client.get(url)
                obj = response.context['page_obj'][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_in_context_for_post_detail_page(self):
        '''При выводе поста с картинкой изображение передаётся
        в словаре context на странице post_detail'''
        response = self.guest_client.get(self.POST_DETAIL_URL)
        obj = response.context['post']
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        '''При отправке поста с картинкой через форму PostForm
        создаётся запись в базе данных.'''
        self.assertTrue(
            Post.objects.filter(text='Тестовый пост',
                                image='posts/small.gif').exists()
        )
