#!/usr/bin/python3
import argparse
import os
import subprocess
import sys

template = '''// +build !debug

package {package}

// {variable} is a byte representation for {fn}
var {variable} = []byte{{{bytes}}}
'''

goosarchs = [
    ('darwin', '386'),
    ('darwin', 'amd64'),
    # # ('darwin', 'arm'),  // not compiling
    # # ('darwin', 'arm64'),  // not compiling
    # ('dragonfly', 'amd64'),
    ('freebsd', '386'),
    ('freebsd', 'amd64'),
    ('freebsd', 'arm'),
    ('linux', '386'),
    ('linux', 'amd64'),
    ('linux', 'arm'),
    ('linux', 'arm64'),
    # ('linux', 'ppc64'),
    # ('linux', 'ppc64le'),
    # ('linux', 'mips'),
    # ('linux', 'mipsle'),
    # ('linux', 'mips64'),
    # ('linux', 'mips64le'),
    # ('netbsd', '386'),
    # ('netbsd', 'amd64'),
    # ('netbsd', 'arm'),
    # ('openbsd', '386'),
    # ('openbsd', 'amd64'),
    # ('openbsd', 'arm'),
    # ('plan9', '386'),
    # ('plan9', 'amd64'),
    # # ('solaris', 'amd64'),  // not compiling
    ('windows', '386'),
    ('windows', 'amd64'),
]

binfiles = [
    ("./static/css/bootstrap.min.css", "FileBootstrapMinCSS"),
    ("./static/css/font-awesome.min.css", "FileFontAwesomeMinCSS"),
    ("./static/img/siridb-large.png", "FileSiriDBLargePNG"),
    ("./static/img/siridb-small.png", "FileSiriDBSmallPNG"),
    ("./static/img/loader.gif", "FileLoaderGIF"),
    ("./static/js/libs/jsleri-1.1.2.min.js", "FileLeriMinJS"),
    ("./static/js/grammar.js", "FileGrammarJS"),
    ("./static/fonts/FontAwesome.otf", "FileFontAwesomeOTF"),
    ("./static/fonts/fontawesome-webfont.eot", "FileFontawesomeWebfontEOT"),
    ("./static/fonts/fontawesome-webfont.svg", "FileFontawesomeWebfontSVG"),
    ("./static/fonts/fontawesome-webfont.ttf", "FileFontawesomeWebfontTTF"),
    ("./static/fonts/fontawesome-webfont.woff", "FileFontawesomeWebfontWOFF"),
    ("./static/fonts/fontawesome-webfont.woff2",
        "FileFontawesomeWebfontWOFF2"),
    ("./static/favicon.ico", "FileFaviconICO"),
    ("./src/index.html", "FileIndexHTML"),
    ("./src/waiting.html", "FileWaitingHTML"),
    ("./build/bundle.min.js", "FileBundleMinJS"),
    ("./build/layout.min.css", "FileLayoutMinCSS"),
]


def get_version(path):
    version = None
    with open(os.path.join(path, 'siridb-http.go'), 'r') as f:
        for line in f:
            if line.startswith('const AppVersion ='):
                version = line.split('"')[1]
    if version is None:
        raise Exception('Cannot find version in siridb-http.go')
    return version


def build_all():
    path = os.path.dirname(__file__)
    version = get_version(path)
    outpath = os.path.join(path, 'bin', version)
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    for goos, goarch in goosarchs:
        tmp_env = os.environ.copy()
        tmp_env["GOOS"] = goos
        tmp_env["GOARCH"] = goarch
        outfile = os.path.join(outpath, 'siridb-http_{}_{}_{}.{}'.format(
            version, goos, goarch, 'exe' if goos == 'windows' else 'bin'))
        with subprocess.Popen(
                ['go', 'build', '-o', outfile],
                env=tmp_env,
                cwd=path,
                stdout=subprocess.PIPE) as proc:
            print('Building {}/{}...'.format(goos, goarch))


def build(development=True):
    path = os.path.dirname(__file__)
    version = get_version(path)
    outfile = os.path.join(path, 'siridb-http_{}.{}'.format(
        version, 'exe' if sys.platform.startswith('win') else 'bin'))
    args = ['go', 'build', '-o', outfile]

    if development:
        args.extend(['--tags', 'debug'])

    with subprocess.Popen(
            args,
            cwd=os.path.dirname(__file__),
            stdout=subprocess.PIPE) as proc:
        print('Building {}...'.format(outfile))


def compile_less():
    path = os.path.dirname(__file__)
    subprocess.run([
        'lessc',
        '--clean-css',
        os.path.join(path, 'src', 'layout.less'),
        os.path.join(path, 'build', 'layout.min.css')])

    subprocess.run([
        'lessc',
        os.path.join(path, 'src', 'layout.less'),
        os.path.join(path, 'build', 'layout.css')])


def webpack():
    print('(be patient, this can take some time)...')
    path = os.path.dirname(__file__)
    env = os.environ
    env['NODE_ENV'] = 'production'
    with subprocess.Popen([
            os.path.join('.', 'node_modules', '.bin', 'webpack'),
            '-p'],
            env=env,
            cwd=os.path.join(path, 'src'),
            stdout=subprocess.PIPE) as proc:
        print(proc.stdout.read().decode('utf-8'))


def compile(fn, variable, empty=False):
    if empty:
        data = ''
    else:
        with open(fn, 'rb') as f:
            data = f.read()
    with open('{}.go'.format(variable.lower()), 'w', encoding='utf-8') as f:
        f.write(template.format(
            package='main',
            fn=fn,
            variable=variable,
            bytes=', '.join(str(c) for c in data)
        ))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-l', '--less',
        action='store_true',
        help='compile less')

    parser.add_argument(
        '-w', '--webpack',
        action='store_true',
        help='compile production webpack')

    parser.add_argument(
        '-g', '--go',
        action='store_true',
        help='compile go files for production')

    parser.add_argument(
        '-e', '--go-empty',
        action='store_true',
        help='compile placeholder go files for development')

    parser.add_argument(
        '-b', '--build',
        action='store_true',
        help='build binary (developemt or production depending on -g or -e)')

    parser.add_argument(
        '-a', '--build-all',
        action='store_true',
        help='build production binaries for all goos and goarchs')

    args = parser.parse_args()

    if args.go and args.go_empty:
        print('Cannot use -e and -g at the same time')
        sys.exit(1)

    if args.less:
        print('Compiling less...')
        compile_less()
        print('Finished compiling less!')

    if args.webpack:
        print('Compiling javascript using webpack...')
        webpack()
        print('Finished compiling javascript using webpack...')

    if args.go:
        print('Create go handler files...')
        for bf in binfiles:
            compile(*bf)
        print('Finished creating go handler files!')

    if args.go_empty:
        print('Create empty go handler files...')
        for bf in binfiles:
            compile(*bf, empty=True)
        print('Finished creating  empty go handler files!')

    if args.build:
        if args.go:
            print('Build production binary')
            build(development=False)
        elif args.go_empty:
            print('Build develpment binary')
            build(development=True)
        else:
            print('Cannot use -b without -e or -g')
            sys.exit(1)
        print('Finished build!')

    if args.build_all:
        build_all()
        print('Finished building binaries!')

    if not any([
            args.go,
            args.go_empty,
            args.less,
            args.webpack,
            args.build_all]):
        parser.print_usage()
