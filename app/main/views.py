#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template
from flask import session
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

from .. import db
from ..models import User              # user table
from ..models import Permission
from ..models import Post
from ..models import Click
from ..models import SiteData
from ..models import StatisticVisitor
from ..models import Machine

from ..email import send_mail

import os
import datetime


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    recent_posts = Post.query.order_by(Post.timestamp.desc()).limit(5)
    sitedata = SiteData.query.filter_by(id=1).first()

    sv = StatisticVisitor.query.filter_by(ip=request.remote_addr).first()

    print 'USER AGENT: %s' % request.user_agent
    print '%s' % type(request.user_agent)
    print '%s' % dir(request.user_agent)
    agent = request.user_agent.browser

    print '%s' % datetime.datetime.utcnow()
    if sv is not None:
        sv.hits += 1
        sv.referred = request.referrer
        sv.agent = agent
        sv.platform = request.user_agent.platform
        sv.version = request.user_agent.version
        sv.last_count = datetime.datetime.utcnow()
    else:
        sv = StatisticVisitor(ip=request.remote_addr,
                              referred=request.referrer,
                              agent=agent,
                              hits=1,
                              platform=request.user_agent.platform,
                              version=request.user_agent.version,
                              last_count=datetime.datetime.utcnow())
    db.session.add(sv)
    db.session.commit()

    if sitedata is not None:
        sitedata.visitor_count += 1
        db.session.add(sitedata)
        db.session.commit()
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
    return render_template('index.html', form=form, posts=posts,
                           pagination=pagination, recent_posts=recent_posts,
                           sitedata=sitedata,
                           sv=sv)


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

@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    if post is None:
        abort(404)
    else:
        post.view_count += 1
        db.session.add(post)
        db.session.commit()
    return render_template('post.html', post=post)


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

@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User.')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You have now following %s.' % username)
    return redirect(url_for('main.user', username=username))

@main.route('/follow/<username>')
@login_required
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User.')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You have now following %s.' % username)
    return redirect(url_for('main.user', username=username))


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

