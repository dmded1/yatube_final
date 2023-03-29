from django.urls import reverse

TEST_SLUG = 'test-slug'
TEST_USER = 'unknown'

INDEX_URL = reverse('posts:index')
GROUP_POSTS_URL = reverse('posts:group_posts', args={'test-slug': TEST_SLUG})
PROFILE_URL = reverse('posts:profile', args={'unknown': TEST_USER})
POST_CREATE_URL = reverse('posts:post_create',)
FOLLOW_INDEX_URL = reverse('posts:follow_index')
