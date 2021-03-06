from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
  name = 'django-model-mutations',         
  packages = ['django_model_mutations'],   
  version = '0.1.1',      
  license='MIT',        
  description = 'Graphene Django mutations for Django models made easier',   
  author = 'Tomáš Opletal',                   
  author_email = 't.opletal@gmail.com',      
  url = 'https://github.com/topletal/django-model-mutations',  
  keywords = ['GRAPHENE', 'GRAPHENE-DJANGO', 'GRAPHQL', 'DJANGO', 'MODELS', 'API'],
  install_requires = [
          'graphene',        
          'graphene-django',
          'django'
      ],
  long_description=long_description,
  long_description_content_type='text/markdown',  
  classifiers=[
    'Development Status :: 3 - Alpha',     
    'Intended Audience :: Developers',      
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',  
    'Environment :: Web Environment',
    'Framework :: Django',
    'Programming Language :: Python :: 3',     
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
)
