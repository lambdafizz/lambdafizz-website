from flask_frozen import Freezer
import wsgi

freezer = Freezer(wsgi.application)

if __name__ == '__main__':
    freezer.freeze()