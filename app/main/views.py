#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template
from flask import redirect
from flask import url_for
from flask import flash
from flask import request
from flask import send_from_directory
from flask import abort
from flask import current_app
from flask import jsonify

from flask.ext.login import login_required
from flask.ext.login import current_user

from . import main

from .forms import PostForm
from .forms import CommentForm
from .forms import VisitorCommentForm
from .forms import EditProfileForm
from .forms import EditProfileAdminForm
from .forms import CategoryForm

from .. import db

from ..models import User              # user table
from ..models import Role
from ..models import Post
from ..models import Comment
from ..models import Category
from ..models import Click
from ..models import SiteData
from ..models import StatisticVisitor

import os
import datetime

# 首页
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    recent_posts = Post.query.order_by(Post.timestamp.desc()).limit(10)
    recent_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(10)
    categories = Category.query.all()

    if form.validate_on_submit():
        title = (form.title.data).encode('UTF-8')
        body = (form.body.data).encode('UTF-8')
        category = Category.query.get(form.category.data)
        post = Post(title=title,
                    body=body,
                    category=category,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        flash('发布成功!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=int(os.environ.get('POST_PER_PAGE', 5)),
        error_out=False)
    posts = pagination.items
    return render_template('index.html',
                           form=form,
                           posts=posts,
                           pagination=pagination,
                           recent_posts=recent_posts,
                           recent_comments=recent_comments,
                           categories=categories,
                           )


# 帖子
@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    comments = Comment.query.order_by(Comment.timestamp.desc())
    if current_user.is_authenticated:
        form = CommentForm()
        author = current_user._get_current_object()
    else:
        form = VisitorCommentForm()
        author = User(username=form.name.data)
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=author)
        db.session.add(comment)
        db.session.commit()
        flash('评论提交成功!')
        return redirect(url_for('.post', id=post.id, page=-1))
    if post is None:
        abort(404)
    else:
        post.view_count += 1
        db.session.add(post)
        db.session.commit()
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) / current_app.config['COMMENT_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page,
                                                                          per_page=current_app.config['COMMENT_PER_PAGE'],
                                                                          error_out=False)
    comments=pagination.items
    return render_template('post.html',
                           post=post,
                           form=form,
                           comments=comments,
                           pagination=pagination)


# 帖子删除
@main.route('/post/delete/<int:id>')
@login_required
def delete(id):
    post=Post.query.get_or_404(id)
    if post is None:
        abort(404)
    db.session.delete(post)
    db.session.commit()
    flash(u'文章删除成功!')
    return redirect(url_for('main.index'))


# 帖子点赞
@main.route('/post/favor', methods=['GET','POST'])
def post_favor():
    print request.method
    print '%s' % dir(request.form)
    print 'POST:%s\n' % request.form['post_id']
    post = Post.query.filter_by(id=request.form['post_id']).first()
    if post is None:
        pass
    else:
        post.favor += 1
        db.session.add(post)
        db.session.commit()

    return jsonify(post_favor=post.favor)


# 帖子归档
@main.route('/post/category')
def category():
    categories = Category.query.all()
    posts = Post.query.all()
    return render_template('category.html',
                           categories=categories,
                           posts=posts)

# 帖子归类
@main.route('/post/category/<int:id>')
def category_post(id):
    posts = Post.query.filter_by(id=id).all()
    if posts is None:
        abort(404)
    return render_template('post_category.html', posts=posts)

# 创建分类
@main.route('/create_category', methods=['GET', 'POST'])
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category.query.filter_by(name=form.category.data).first()
        if category is not None:
            flash('该分类已存在！请重新添加。')
            form.category.data = ''
            return redirect(url_for('main.create_category'))
        category = Category(name=form.category.data)
        db.session.add(category)
        db.session.commit()
        flash('分类添加成功!')
    return render_template('create_category.html', form=form)

# 用户资料
@main.route('/user/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(403)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


# 用户资料编辑
@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        current_user.username = form.username.data
        db.session.add(current_user)
        db.session.commit()
        flash('资料更新成功!')
        return redirect(url_for('main.user_profile', username=current_user.username))
    form.username.data = current_user.username
    form.about_me.data = current_user.about_me
    form.location.data = current_user.location
    return render_template('edit_profile.html', form=form)


# 管理员级别的用户资料编辑
@main.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('资料更新成功!')
        return redirect(url_for('main.user_profile', username=user.username))
    form.email.data = user.email
    form.username = user.username
    form.confirmed = user.confirmed
    form.role.data = user.role
    form.location.data = user.location
    form.about_me = user.about_me
    return render_template('edit_profile.html', form=form)


# 简历下载页面
@main.route('/download')
def download():
    url = os.path.join('/download/', 'my_resume.pdf')
    c = Click.query.filter_by(url_name=url).first()
    if c is None:
        count = 0
    else:
        count = c.click_count
    return render_template('download.html', count=count)


# 简历下载并统计下载次数
@main.route('/download/<path:filename>')
def download_file(filename):
    url = os.path.join('/download/', filename)
    c = Click.query.filter_by(url_name=url).first()
    if c is None:
        c = Click(url_name=url, click_count=1)
    else:
        c.click_count += 1
    db.session.add(c)
    db.session.commit()
    return send_from_directory(os.environ.get('DOWNLOAD_FOLDER'), filename, as_attachment=True)


# 关注用户
@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('关注失败！')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('已经关注该用户！')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('已关注用户 %s.' % username)
    return redirect(url_for('main.user', username=username))


# 取关关注
@main.route('/follow/<username>')
@login_required
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在或取关失败！')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You have now following %s.' % username)
    return redirect(url_for('main.user', username=username))


# 关注用户列表
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()

    if user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=10, error_out=False
    )
    follows = [{'user': item.followers, 'timestamp': item.timestamp}
               for item in pagination.items]

    return render_template('followers.html', user=user,
                           title="Followers of", endpoint='main.followers',
                           pagination=pagination, follows=follows)