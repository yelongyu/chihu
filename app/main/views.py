#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template, session, redirect, url_for, flash, request, send_from_directory, abort, current_app
from flask.ext.login import login_required, current_user

from . import main
from .forms import PostForm
from .. import db
from ..models import User, Permission, Post, Click
from ..email import send_mail

import os
import datetime


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    recent_posts = Post.query.order_by(Post.timestamp.desc()).limit(5)
    print 'RECENT POST: %r' % recent_posts
    if recent_posts is not None:
        for post in recent_posts:
            print 'title: %s\n' % post.id
    if form.validate_on_submit():
        title = (form.title.data).encode('UTF-8')
        body = (form.body.data).encode('UTF-8')
        post = Post(title=title, body=body, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        flash('Post success!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=int(os.environ.get('POST_PER_PAGE', 5)),
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination, recent_posts=recent_posts)


@main.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(403)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@main.route('/modify/city', methods=['GET', 'POST'])
def modify_city():
    city = request.form['city']
    print 'city = %s' % city
    user = current_user
    user.location = city
    db.session.add(user)
    db.session.commit()
    return render_template('user.html', user=current_user)

@main.route('/download')
def download():
    url = os.path.join('/download/', 'my_resume.pdf')
    print 'URL=%s' % url
    c = Click.query.filter_by(url_name=url).first()
    if c is None:
        count = 0
    else:
        count = c.click_count
    return render_template('download.html', count=count)

@main.route('/download/<path:filename>')
def download_file(filename):
    url = os.path.join('/download/', filename)
    print 'URL = %s' % url
    c = Click.query.filter_by(url_name=url).first()
    print 'c = %s' % c
    if c is None:
        c = Click(url_name=url, click_count=1)
    else:
        c.click_count += 1
    db.session.add(c)
    db.session.commit()
    return send_from_directory(os.environ.get('DOWNLOAD_FOLDER'), filename, as_attachment=True)


@main.route('/about_me')
def about_me():
    return render_template('about_me.html')

@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    if post is None:
        abort(404)
    return render_template('post.html', post=post)
