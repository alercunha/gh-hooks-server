import argparse
import hashlib
import hmac
import json
import logging
import os
import subprocess

from tornado import web, ioloop
from tornado.web import HTTPError


def create_handler(project_map: dict, secret: str=None):
    logging.info('Validate X-Hub-Signature: {0}'.format(secret is not None))

    class AutoPullHandler(web.RequestHandler):
        def post(self, key):
            if secret:
                digest = hmac.new(secret.encode(), self.request.body, hashlib.sha1).hexdigest()
                sig = self.request.headers.get('X-Hub-Signature', 'sha1=')[5:]
                if not hmac.compare_digest(sig, digest):
                    logging.debug('{0} <> {1}'.format(sig, digest))
                    raise HTTPError(401, 'Wrong signature')

            if key not in project_map:
                raise HTTPError(404, 'Project {0} not found'.format(key))
            logging.info('Updating {0}: {1}'.format(key, project_map[key]))
            output = subprocess.check_output(['git', 'pull'], cwd=project_map[key], stderr=subprocess.STDOUT).decode().strip()
            logging.info('Output: {0}'.format(output))
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({'output': output}))
            self.write(os.linesep)

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

    return AutoPullHandler


def parse_projects(projects: list):
    map = {}
    for project in projects:
        split = project.split('=')
        if not os.path.isdir(split[1]):
            raise NotADirectoryError('Path {0} not found'.format(split[1]))
        logging.info('Mapped {0} to {1}'.format(split[0], split[1]))
        map[split[0]] = split[1]
    return map


def run(args):
    project_map = parse_projects(args.projects)
    handlers = [
        ('/autopull/(\w+)/?', create_handler(project_map, args.secret)),
    ]
    app = web.Application(handlers)
    logging.info('Listening on port {0}...'.format(args.port))
    app.listen(args.port)
    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('tornado.access').setLevel(logging.WARN)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', help='HTTP port to listen (default 8011)', default=8011, type=int)
    parser.add_argument(
        '-a',
        action='append',
        dest='projects',
        default=[],
        help='Add a project path to be monitored (format key=path)'
    )
    parser.add_argument('--secret', help='A secret that validates X-Hub-Signature')
    args = parser.parse_args()
    if len(args.projects) == 0:
        parser.print_help()
        exit(1)
    try:
        run(args)
    except NotADirectoryError as e:
        logging.error(e)
        exit(1)

