from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch


class PostQuerySet(models.QuerySet):
    def popular(self):
        most_popular_posts = self.annotate(
            likes_count=Count('likes', distinct=True)).order_by('-likes_count')
        return most_popular_posts

    def fetch_with_comments_count(self):
        posts_with_comments = Post.objects.filter(
            id__in=self
        ).annotate(
            total_comments=Count('comments')
        )
        post_ids_and_comments = dict(
            posts_with_comments.values_list('id', 'total_comments')
        )
        for post in self:
            post.total_comments = post_ids_and_comments[post.id]
        return self

    # def fresh(self):
    #     fresh_posts = self.order_by('-published_at')
    #     return fresh_posts

    def fetch_with_tag_count(self):
        most_popular_tags = self.prefetch_related(
            Prefetch('tags', queryset=Tag.objects.popular()))
        return most_popular_tags


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')
    objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class TagQuerySet(models.QuerySet):

    def popular(self):
        most_popular_tags = self.annotate(
            posts_count=Count('posts')).order_by('-posts_count')
        return most_popular_tags


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)
    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост, к которому написан')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
