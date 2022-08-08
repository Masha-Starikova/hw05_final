from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from .models import Follow, Post, User, Group, Comment
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm


def get_page(queryset, request):
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20)
def index(request):
    posts = Post.objects.all().select_related(
        'group',
        'author',
    )
    page_obj = get_page(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = get_page(posts, request)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_post = Post.objects.filter(author=author)
    page_obj = get_page(author_post, request)
    following = (
        request.user.is_authenticated and author.following.filter(
            user=request.user).exists()
    )
    if following:
        following = True
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.select_related('post').filter(post=post)
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST, files=request.FILES or None
        )
        context = {
            'form': form,
        }
        if form.is_valid():
            form = form.save(commit=False)
            form.author = request.user
            form.save()
            return redirect('posts:profile', request.user.username)
        return render(request, 'posts/create_post.html', context)
    form = PostForm()
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_edit = True
    if request.user.id == post.author.id:
        if request.method == 'POST':
            form = PostForm(
                request.POST or None,
                files=request.FILES or None,
                instance=post
            )
            if form.is_valid():
                post.save()
                return redirect('posts:post_detail', post.id)
            context = {
                'form': form,
                'is_edit': is_edit,
            }
            return render(request, 'posts/create_post.html', context)
        else:
            form = PostForm(instance=post)
            context = {
                'form': form,
                'is_edit': is_edit,
            }
            return render(request, 'posts/create_post.html', context)
    return redirect('posts:post_detail', post.id)


@login_required
def follow_index(request):
    follow_author_posts = Post.objects.filter(
        author__following__user=request.user)
    # Объявляем страницу с пагинацией
    page_obj = get_page(follow_author_posts, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and not follower.exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect('posts:profile', username=author)
