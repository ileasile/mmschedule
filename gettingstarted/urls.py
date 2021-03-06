from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import hello.views
import mmschedule.bot
import mmschedule.sethook

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', hello.views.index, name='index'),
    url(r'^db', hello.views.db, name='db'),
    url(r'^admin/', include(admin.site.urls)),
	url(r'^mmschedule', mmschedule.bot.process_request, name='hi'),
	url(r'^sethook', mmschedule.sethook.sethook, name='sethook'),
]
