import argparse
import hashlib
import hmac
import json
import logging
import os
import subprocess

from tornado import web, ioloop
from tornado.web import HTTPError


def create_handler(mappings: list, secret: str=None):
    logging.info('Validate X-Hub-Signature: {0}'.format(secret is not None))

    class WebhookHandler(web.RequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.processes = []

        def post(self, key):
            if secret:
                self.validate_signature()

            targets = [i[1] for i in mappings if i[0] == key]
            if len(targets) == 0:
                raise HTTPError(404, 'No mapping found for key: {0}'.format(key))
            for target in targets:
                if not os.path.isfile(target):
                    raise FileNotFoundError('File {0} not found'.format(target))
                cwd = os.path.dirname(target)
                logging.info('Executing mapping {0}: {1}'.format(key, target))
                p = subprocess.Popen(['bash', target], cwd=cwd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
                self.processes.append(p)
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({'success': True}))
            self.write(os.linesep)
            self.finish()

        def on_finish(self):
            for p in self.processes:
                logging.info('=== process output ===')
                out, err = p.communicate()
                logging.info('{0}{1}'.format(os.linesep, (out or b'None').decode().strip()))
                logging.info('=== done ===')

        def write_error(self, status_code, **kwargs):
            msg = ''
            if 'exc_info' in kwargs:
                exception = kwargs['exc_info'][1]
                msg = str(exception)
                self.set_header('Content-Type', 'application/json')
                self.finish(json.dumps({'error-message': msg}))
            else:
                super().write_error(status_code, **kwargs)
            logging.warning('status: {0} - {1}'.format(status_code, msg))

        def validate_signature(self):
            digest = hmac.new(secret.encode(), self.request.body, hashlib.sha1).hexdigest()
            sig = self.request.headers.get('X-Hub-Signature', 'sha1=')[5:]
            if not hmac.compare_digest(sig, digest):
                logging.debug('{0} <> {1}'.format(sig, digest))
                raise HTTPError(401, 'Wrong signature')

    return WebhookHandler


def run(args):
    mappings = [i.split(':') for i in args.mappings]
    logging.info('Mappings: {0}'.format(args.mappings))
    handlers = [
        ('/ghhooks/(\w+)/?', create_handler(mappings, args.secret)),
    ]
    app = web.Application(handlers)
    logging.info('Listening on port {0}...'.format(args.port))
    app.listen(args.port)
    ioloop.IOLoop.instance().start()


def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('tornado.access').setLevel(logging.WARN)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', help='HTTP port to listen (default 8011)', default=8011, type=int)
    parser.add_argument(
        '-a',
        action='append',
        dest='mappings',
        default=[],
        help='Add a new path mapping from a url path to a bash script (format key:path)'
    )
    parser.add_argument('--secret', help='A secret that validates X-Hub-Signature')
    args = parser.parse_args()
    if len(args.mappings) == 0:
        parser.print_help()
        exit(1)
    try:
        run(args)
    except NotADirectoryError as e:
        logging.error(e)
        exit(1)


if __name__ == '__main__':
    main()
