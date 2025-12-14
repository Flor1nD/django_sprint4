from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView
)
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib import messages

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserForm, RegistrationForm

User = get_user_model()


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10
    context_object_name = 'page_obj'

    def get_queryset(self):
        queryset = Post.objects.select_related(
            'author', 'location', 'category'
        ).prefetch_related('comments')

        queryset = queryset.filter(
            Q(is_published=True) &
            Q(category__is_published=True) &
            Q(pub_date__lte=timezone.now())
        )

        queryset = queryset.order_by('-pub_date')

        return queryset

    def get_context_data(self, **kwargs):
        """Добавляем дополнительную информацию в контекст"""
        context = super().get_context_data(**kwargs)

        # Добавляем информацию о текущем пользователе
        context['user'] = self.request.user

        # Логируем контекст для отладки
        print(f"DEBUG: В контекст передано {len(context.get('posts', []))} постов")

        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'author', 'location', 'category'
        ).annotate(comment_count_annotated=Count('comments'))  # Изменяем имя

        if self.request.user.is_authenticated:
            post = queryset.first()
            if post and self.request.user == post.author:
                return queryset
        return queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        # Добавляем comment_count для шаблона
        context['post'].comment_count = self.object.comments.count()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        has_categories = Category.objects.filter(is_published=True).exists()
        context['has_categories'] = has_categories
        if not has_categories:
            messages.warning(
                self.request,
                'Нет доступных категорий. Пожалуйста, создайте категории через админ-панель.'
            )
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        post = self.get_object()
        return redirect('blog:post_detail', pk=post.pk)

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.object.pk])


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        post = self.get_object()
        return redirect('blog:post_detail', pk=post.pk)


class CategoryPostListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10
    context_object_name = 'page_obj'

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

        queryset = Post.objects.select_related(
            'author', 'location', 'category'
        ).filter(
            category=self.category,
            is_published=True,
            category__is_published=True,  # Двойная проверка
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.select_related(
            'location', 'category'
        ).order_by('-pub_date')

        # Создаем пагинатор
        paginator = Paginator(posts, 10)  # 10 постов на страницу
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['is_paginated'] = paginator.num_pages > 1
        return context


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def test_func(self):
        return self.request.user.username == self.kwargs['username']

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
    return redirect('blog:post_detail', pk=post_id)


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' in context:
            del context['form']
        return context

def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration/registration_form.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('blog:index')
