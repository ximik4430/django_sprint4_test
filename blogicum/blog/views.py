from blog.forms import CommentForm, PostForm, ProfileForm
from blog.models import Category, Comment, Post
from blog.utils import post_all_query, post_published_query
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)


class MainPostListView(ListView):
    """Главная страница со списком постов."""

    model = Post
    template_name = 'blog/index.html'
    queryset = post_published_query()
    paginate_by = 10


class ProfileLoginView(LoginView):
    def get_success_url(self):
        url = reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )
        return url


class EditProfileUserView(LoginRequiredMixin, UpdateView):
    """Изменение профиля пользователя."""

    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        username = self.request.user
        return reverse("blog:profile", kwargs={"username": username})


class UserPostsListView(MainPostListView):
    """Информация о пользователе."""
    template_name = 'blog/profile.html'
    author = None

    def get_queryset(self):
        username = self.kwargs['username']
        self.author = get_object_or_404(User, username=username)
        if self.author == self.request.user:
            return post_all_query().filter(author=self.author)
        return super().get_queryset().filter(author=self.author)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = Post.objects.select_related('author')
        paginator = Paginator(post, 10)
        page_obj = paginator.get_page(post)
        context['profile'] = self.author
        context['page_obj'] = page_obj
        return context

    def get_page(self, queryset):
        paginator = Paginator(queryset, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        for post in page_obj:
            post.comment_count = post.comments.count()
        return page_obj


class PostListView(ListView):
    template_name = 'blog/index.html'
    model = Post
    ordering = '-pub_date'
    paginate_by = 10

    def get_queryset(self):
        query_set = post_all_query().filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
        return query_set


def category_posts(request, category_slug):
    """Отображение по категории постов"""
    templates = 'blog/category.html'
    current_time = timezone.now()
    category = get_object_or_404(
        Category,
        is_published=True,
        slug=category_slug
    )
    post_list = category.posts.filter(
        pub_date__lte=current_time,
        is_published=True,
    ).select_related('category')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, templates, context)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Проверка валидности формы."""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Получение адреса."""
        url = reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )
        return url


class DispatchMixin:
    def dispatch(self, request, *args, **kwargs):
        """Отправляет изменения/удаления поста"""
        self.post_id = kwargs['pk']
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', pk=self.post_id)
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(LoginRequiredMixin, DispatchMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        """Получение адреса."""
        url = reverse('blog:post_detail', args=(self.post_id,))
        return url


class PostDeleteView(LoginRequiredMixin, DispatchMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:index')
    template_name = 'blog/create.html'


class PostDetailView(DetailView):
    """Страница выбранного поста."""
    model = Post
    template_name = "blog/detail.html"
    post_data = None

    def get_queryset(self):
        self.post_data = get_object_or_404(Post, pk=self.kwargs["pk"])
        if self.post_data.author == self.request.user:
            return post_all_query().filter(pk=self.kwargs["pk"])
        return post_published_query().filter(pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.check_post_data():
            context["flag"] = True
            context["form"] = CommentForm()
        context["comments"] = self.object.comments.all().select_related(
            "author"
        )
        return context

    def check_post_data(self):
        """Вернуть результат проверки поста."""
        return all(
            (
                self.post_data.is_published,
                self.post_data.pub_date,
                self.post_data.category.is_published,
            )
        )


@login_required
def add_comment(request, pk):
    """Добавление комментария"""
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=pk)


@login_required
def edit_comment(request, comment_id, post_id):
    """Изменение комментария"""
    instance = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    form = CommentForm(request.POST or None, instance=instance)
    if instance.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    context = {
        'form': form,
        'comment': instance
    }

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', pk=post_id)
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, comment_id, post_id):
    """Удаление комментария"""
    instance = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if instance.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    context = {'comment': instance}
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', pk=post_id)
    return render(request, 'blog/comment.html', context)
