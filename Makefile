pypi:
	python setup.py sdist upload -s 

clean:
	rm -rf dist build *egg-info
	find . -name "*.pyc" | xargs rm

build-jenkins-virtualenv:
	pip install -e .
	pip install $(DBA_SQL_PACKAGE) coverage pylint
	pip install psycopg2==2.4.1

test:
	cd nosedjangotests && nosetests --verbosity=3 --with-xunit --with-doctest --with-django --django-settings nosedjangotests.settings --with-django-testfs --debug="nose.plugins.nosedjango" --with-coverage nosedjangotests.polls

test-sqlite:
	cd nosedjangotests && nosetests --verbosity=3 --with-xunit --with-doctest --with-django --django-settings nosedjangotests.settings --with-django-testfs --with-django-sqlite --debug="nose.plugins.nosedjango" --with-coverage nosedjangotests.polls

