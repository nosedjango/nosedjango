pypi:
	python setup.py sdist upload -s 

clean:
	rm -rf dist build *egg-info
	find . -name "*.pyc" | xargs rm

test:
	nosetests --verbosity=3 --with-xunit --with-doctest --with-django --django-settings nosedjangotests.settings --with-django-testfs --debug="nose.plugins.nosedjango" --with-coverage nosedjangotests.polls

test-sqlite:
	nosetests --verbosity=3 --with-xunit --with-doctest --with-django --django-settings nosedjangotests.settings --with-django-testfs --with-django-sqlite --debug="nose.plugins.nosedjango" --with-coverage nosedjangotests.polls

