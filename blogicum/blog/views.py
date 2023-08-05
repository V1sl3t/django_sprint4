from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .constans import POSTS_NUMBER
from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

User = get_user_model()


class ProfileListView(ListView):
    model = User
    template_name = 'blog/profile.html'
    ordering = 'id'
    paginate_by = POSTS_NUMBER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context

    def get_queryset(self):
        return Post.objects.filter(
            author__username=self.kwargs['username']
        ).select_related(
            'location', 'category', 'author'
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')


class ProfileUpdateView(UpdateView, LoginRequiredMixin):
    model = User
    fields = ('username', 'first_name', 'last_name', 'email')
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(User, username=self.kwargs['username'])
        if instance.username != self.request.user.username:
            return redirect('blog:index')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(LoginRequiredMixin, PostMixin, UpdateView):

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:index')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PostForm(instance=self.object)
        context['form'] = form
        return context


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    ordering = 'id'
    paginate_by = POSTS_NUMBER

    def get_queryset(self):
        return Post.objects.select_related(
            'category',
            'location',
            'author').filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(Post.objects.select_related(
            'category',
            'location',
            'author'),
            pk=self.kwargs['pk']
        )
        if self.object.author != self.request.user:
            context['post'] = get_object_or_404(Post.objects.select_related(
                'category',
                'location',
                'author').filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()),
                pk=self.kwargs['pk'],
            )
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ('text',)
    template_name = 'blog/comments.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, id=kwargs['comment_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    pass


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/index.html'
    ordering = 'id'
    paginate_by = POSTS_NUMBER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(Category.objects.filter(
            is_published=True),
            slug=self.kwargs['category_slug']
        )
        return context

    def get_queryset(self):
        return Post.objects.select_related(
            'category',
            'location',
            'author').filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__slug=self.kwargs['category_slug']).annotate(
            comment_count=Count('comments')).order_by(
            '-pub_date')
