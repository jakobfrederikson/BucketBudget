from flask import render_template

def forbidden(e):
    return render_template('errors/403.html'), 403

def page_not_found(e):
    return render_template('errors/404.html'), 404